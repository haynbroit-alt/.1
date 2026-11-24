"""Assemblage du rapport de l'entreprise mère et rendu du tableau de bord commercial (public et privé)."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from . import chaine, sources, stripe
from .faits import INDICATEURS, TOUTE_L_ENTREPRISE, Fait
from .portefeuille import CRITERES, LIBELLES_CRITERES, Opportunite, charger
from .statuts import CONFLIT, ECHEC, INCONNU, PROUVE, combiner

INDICATEURS_OBLIGATOIRES = ("visiteurs", "prospects_contactes", "envois_bloques", "reponses", "prospects_qualifies",
                            "conversions", "ventes_payees", "paiements_echoues", "remboursements", "couts",
                            "frais_paiement", "benefice_net", "ca_annonce", "encaisse_net", "abonnements_actifs",
                            "offres_actives")
LIBELLES = {"visiteurs": "Visiteurs", "prospects_contactes": "Prospects contactés",
            "envois_bloques": "Envois bloqués par un filtre", "reponses": "Réponses",
            "prospects_qualifies": "Prospects qualifiés", "conversions": "Conversions (proposition acceptée)",
            "ventes_payees": "Ventes payées", "paiements_echoues": "Paiements échoués",
            "remboursements": "Remboursements", "couts": "Coûts directs", "frais_paiement": "Frais de paiement",
            "benefice_net": "Bénéfice net (hors temps)", "ca_annonce": "CA annoncé (factures non payées)",
            "encaisse_net": "Argent encaissé net", "abonnements_actifs": "Abonnements actifs",
            "offres_actives": "Offres avec un prix actif", "heures": "Heures du fondateur"}


@dataclass
class Rapport:
    jour: date
    genere: str
    opportunites: list[Opportunite]
    faits: list[Fait]
    consolide: chaine.Consolide
    etats: dict[str, dict[str, tuple[str, str]]]
    arrets: dict[str, list[chaine.EtatArret]]
    priorites: list[Opportunite]
    conflits: list[str]
    alertes: list[str]
    sources_lues: list[tuple[str, str, str]]
    erreurs: list[str]
    declares: dict[str, str] = field(default_factory=dict)
    montants_publics: set[str] = field(default_factory=set)


def _resoudre(racine: Path, candidats: list[str]) -> Path | None:
    for c in candidats:
        p = (racine / c).resolve()
        if p.is_dir():
            return p
    return None


def _fichier(racine: Path, depots: dict[str, Path | None], spec: dict[str, str]) -> Path | None:
    if spec.get("depot"):
        base = depots.get(spec["depot"])
        return base / spec["chemin"] if base else None
    return racine / spec["chemin"]


def construire(racine: Path, jour: date, lire_stripe: bool = False, rejouer: bool = False,
               client: stripe.ClientLecture | None = None) -> Rapport:
    """Lit toutes les sources, consolide, évalue la chaîne. N'écrit que les instantanés privés et les rejeux."""
    erreurs: list[str] = []
    alertes: list[str] = []
    lues: list[tuple[str, str, str]] = []
    config = tomllib.loads((racine / "donnees/sources.toml").read_text(encoding="utf-8"))
    opportunites, reglages, err = charger(racine / "donnees/portefeuille.toml")
    erreurs += err
    depots = {nom: _resoudre(racine, cands) for nom, cands in config.get("depots", {}).items()}
    for nom, chemin in depots.items():
        lues.append((f"dépôt {nom}", "trouvé" if chemin else "absent", ""))
    fichiers = {k: _fichier(racine, depots, v) for k, v in config.get("fichiers", {}).items()}
    faits: list[Fait] = []
    ids = [o.id for o in opportunites]

    # Amélioration continue : prévisions et verdicts du poste business.
    previsions = sources.lire_previsions(fichiers.get("previsions"))
    lues.append(("prévisions (poste business)", "lu" if previsions is not None else "illisible",
                 f"{len(previsions or [])} prévision(s)"))
    rattachement = {pid: o.id for o in opportunites for pid in o.previsions}
    faits += sources.faits_verdicts(previsions, rattachement, jour, "memoire/PREDICTIONS.csv (poste business)")

    # Acheteurs : pipeline privé, chaque ligne avec sa preuve.
    evenements, err = sources.lire_pipeline(fichiers.get("pipeline"))
    erreurs += err
    lues.append(("pipeline commercial (privé)", "lu" if evenements is not None else "absent",
                 f"{len(evenements or [])} événement(s)"))
    faits += sources.faits_pipeline(evenements, ids, "prive/pipeline.csv")
    faits.append(Fait("compteur", "visiteurs", None, INCONNU, "aucun compteur de visites activé",
                      note="à activer sur les pages d'offre avant toute campagne"))

    # Coûts.
    couts, err = sources.lire_couts(fichiers.get("couts"), "prive/couts.csv")
    erreurs += err
    faits += couts
    lues.append(("journal des coûts (privé)", "lu" if couts and couts[0].statut != INCONNU else "absent", ""))

    # Argent : le prestataire de paiement, en lecture seule ; à défaut, le dernier relevé privé daté.
    instantane = racine / "prive/stripe.json"
    correspondances = {o.id: o.stripe_produits for o in opportunites if o.stripe_produits}
    encaissements: list[tuple[str, int, str]] | None = None
    if lire_stripe:
        r = stripe.releve(client or stripe.ClientLecture(), correspondances, str(reglages.get("devise", "eur")),
                          opportunites=ids)
        erreurs += [f"stripe : {e}" for e in r.erreurs]
        stripe_faits, encaissements = r.faits, r.encaissements
        if not any(f.indicateur == "encaisse_net" and f.statut == INCONNU for f in r.faits):
            instantane.parent.mkdir(exist_ok=True)
            instantane.write_text(json.dumps({"faits": [f.to_dict() for f in r.faits],
                                              "encaissements": r.encaissements}, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
        lues.append(("prestataire de paiement", "lu en direct" if not r.erreurs else "lu en partie",
                     "; ".join(r.erreurs)[:120]))
    elif instantane.is_file():
        brut = json.loads(instantane.read_text(encoding="utf-8"))
        stripe_faits = [Fait(**f) for f in brut["faits"]]
        encaissements = [tuple(e) for e in brut["encaissements"]]  # type: ignore[misc]
        quand = stripe_faits[0].date[:10] if stripe_faits else "?"
        lues.append(("prestataire de paiement", f"relevé privé du {quand}", "relancer avec --stripe"))
    else:
        stripe_faits = [Fait("stripe", "encaisse_net", None, INCONNU, "prestataire non relu", prive=True),
                        Fait("stripe", "ventes_payees", None, INCONNU, "prestataire non relu")]
        lues.append(("prestataire de paiement", "non relu", "relancer avec --stripe"))
    faits += stripe_faits

    # Bénéfice net : PROUVÉ seulement si encaissé, frais et coûts le sont tous. Un coût inconnu n'est pas nul.
    c0 = chaine.consolider(faits)
    for cle in [TOUTE_L_ENTREPRISE, *ids]:
        enc, couts_v = chaine.lire(c0, cle, "encaisse_net"), chaine.lire(c0, cle, "couts")
        frais = chaine.lire(c0, cle, "frais_paiement")
        if cle != TOUTE_L_ENTREPRISE and enc.statut == PROUVE and enc.valeur == 0:
            frais = chaine.Valeur(0, PROUVE)
        statut = combiner([enc.statut, couts_v.statut, frais.statut])
        if statut == PROUVE:
            valeur = int(enc.valeur) - int(frais.valeur) - int(couts_v.valeur)  # type: ignore[arg-type]
            faits.append(Fait("mere", "benefice_net", valeur, PROUVE, "calcul : encaissé − frais − coûts", cle,
                              jour.isoformat(), "faits consolidés du même passage", prive=True))
        else:
            faits.append(Fait("mere", "benefice_net", None, statut, "calcul : encaissé − frais − coûts", cle,
                              jour.isoformat(), note="une composante n'est pas prouvée", prive=True))

    # Rejeu des suites de tests des modules (produit) : PROUVÉ seulement sur le commit actuel.
    etat_rejeux = racine / "etat/rejeux.json"
    if rejouer:
        resultats = [sources.rejouer(r["nom"], depots.get(r["depot"]), list(r["commande"]), r["bilan"],
                                     int(r.get("delai", 900))) for r in config.get("rejeu", [])]
        etat_rejeux.parent.mkdir(exist_ok=True)
        etat_rejeux.write_text(json.dumps(resultats, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    else:
        resultats = json.loads(etat_rejeux.read_text(encoding="utf-8")) if etat_rejeux.is_file() else []
    depots_rejeux = {r["nom"]: depots.get(r["depot"]) for r in config.get("rejeu", [])}
    rattach_rejeux: dict[str, list[str]] = {}
    for o in opportunites:
        if o.rejeu:
            rattach_rejeux.setdefault(o.rejeu, []).append(o.id)
    faits += sources.faits_rejeux(resultats, depots_rejeux, rattach_rejeux)
    lues.append(("rejeux des suites de tests", "rejoués" if rejouer else "dernier état", f"{len(resultats)} suite(s)"))

    # Rapprochement : ce que les modules déclarent contre ce que la source qui fait foi montre.
    declarations: list[sources.Declaration] = []
    for cle, lecteur in (("tableau_novarys", sources.declarations_novarys), ("kpi_velyx", sources.declarations_velyx)):
        decl, err = lecteur(fichiers.get(cle))
        declarations += decl
        lues.append((cle.replace("_", " "), "lu" if decl else "absent ou vide", "; ".join(err)[:120]))
    modules = {o.id: o.module for o in opportunites}
    controle, al = chaine.rapprocher(declarations, encaissements, evenements, modules)
    faits += controle
    alertes += al
    conflits = [f.note for f in controle if f.statut == CONFLIT]

    # Statuts déclarés dans les registres des modules contre l'activité réelle.
    tables: dict[str, dict[str, str] | None] = {}
    declares: dict[str, str] = {}
    activite = sources.activite_recente(evenements, jour)
    for o in opportunites:
        if not o.declare:
            if o.statut_mere in ("actif", "test"):
                alertes.append(f"{o.id} : aucun registre de module ne déclare cette offre (responsable : {o.module})")
            continue
        spec = {"depot": o.declare.get("depot", ""), "chemin": o.declare.get("fichier", "")}
        chemin = _fichier(racine, depots, spec)
        cle = str(chemin)
        if cle not in tables:
            tables[cle] = sources.lire_tableau_markdown(chemin)
        table = tables[cle] or {}
        ligne = next((v for k, v in table.items() if o.declare.get("ligne", "\0").lower() in k.lower()), None)
        declares[o.id] = sources.normaliser_statut(ligne) if ligne else "absent"
        if ligne is None:
            alertes.append(f"{o.id} : absent du registre {o.declare.get('fichier')} : opportunité sans déclaration")
        conflit = chaine.conflits_de_statut(o, declares[o.id], activite.get(o.id, 0))
        if conflit:
            conflits.append(conflit)
    for o in opportunites:
        if o.statut_mere in ("actif", "test") and not activite.get(o.id) and evenements is not None:
            alertes.append(f"{o.id} : active, mais aucun envoi ces 14 derniers jours")
        if o.statut_mere in ("gele", "arrete") and activite.get(o.id):
            alertes.append(f"{o.id} : {o.statut_mere} pour la mère, {activite[o.id]} envoi(s) récent(s) : "
                           f"répondre aux retours, ne plus relancer")

    consolide = chaine.consolider(faits)
    arrets = {o.id: chaine.evaluer_arrets(o, consolide, jour, previsions) for o in opportunites}
    etats = {o.id: chaine.etats_chaine(o, consolide, arrets[o.id]) for o in opportunites}
    for o in opportunites:
        for a in arrets[o.id]:
            if a.detail == "verdict dû sans mesure":
                alertes.append(f"{o.id} : verdict dû sans mesure ({a.libelle})")
    prio = chaine.priorites([(o, etats[o.id]) for o in opportunites])
    publics = {str(m) for m in reglages.get("montants_publics", [])}
    return Rapport(jour, datetime.now(UTC).isoformat(timespec="minutes"), opportunites, faits, consolide, etats,
                   arrets, prio, conflits, alertes, lues, erreurs, declares, publics)


# -- Rendu ----------------------------------------------------------------------------------------------

def euros(centimes: int | float | str | bool | None) -> str:
    if not isinstance(centimes, int) or isinstance(centimes, bool):
        return "?"
    signe = "−" if centimes < 0 else ""
    e, c = divmod(abs(centimes), 100)
    return f"{signe}{e:,}".replace(",", " ") + f",{c:02d} €"


def _valeur(v: chaine.Valeur, indicateur: str, prive: bool) -> str:
    if v.valeur is None:
        return "—"
    if INDICATEURS[indicateur][1] == "centimes":
        return euros(v.valeur) if prive else "[privé]"
    return str(v.valeur)


def _note(f: list[Fait]) -> str:
    notes = sorted({x.note for x in f if x.note})
    return "; ".join(notes)


def rendre(r: Rapport, prive: bool) -> str:
    c = r.consolide
    out: list[str] = []
    titre = "privé" if prive else "public"
    out.append(f"# Tableau de bord commercial de l'entreprise mère ({titre})\n")
    out.append(f"> Généré par `python3 -m mere tableau` le {r.genere} (jour évalué : {r.jour.isoformat()}). "
             "Ne pas modifier à la main.")
    if not prive:
        out.append("> Version publique : les montants sont dans `prive/TABLEAU_PRIVE.md`, jamais versionnés.")
    enc = chaine.lire(c, TOUTE_L_ENTREPRISE, "encaisse_net")
    out.append("\n## Verdict\n")
    if enc.statut == PROUVE:
        atteint = isinstance(enc.valeur, int) and enc.valeur > 0
        out.append(f"**Premier euro : {'atteint' if atteint else 'non atteint'}** (PROUVÉ par le prestataire de "
                 f"paiement{', ' + euros(enc.valeur) if prive else ''}). "
                 f"Conflits ouverts : {len(r.conflits)}. Alertes : {len(r.alertes)}.")
    else:
        out.append(f"**Premier euro : {enc.statut}** : l'argent encaissé n'a pas pu être prouvé dans ce passage.")

    out.append("\n## Indicateurs obligatoires (toute l'entreprise)\n")
    out.append("| Indicateur | Valeur | Statut | Sources | Note |")
    out.append("|---|---:|---|---|---|")
    for ind in INDICATEURS_OBLIGATOIRES:
        v = chaine.lire(c, TOUTE_L_ENTREPRISE, ind)
        out.append(f"| {LIBELLES[ind]} | {_valeur(v, ind, prive)} | {v.statut} | {', '.join(v.sources) or '—'} | "
                 f"{_note(v.faits)} |")

    out.append("\n## La chaîne, opportunité par opportunité\n")
    out.append("PROUVÉ = étape franchie avec preuve · INCONNU = pas encore prouvé · ÉCHEC = critère d'arrêt manqué · "
             "CONFLIT = sources contradictoires. Distance = étapes non prouvées avant l'argent encaissé.\n")
    out.append("| Opportunité | Statut mère | " + " | ".join(chaine.LIBELLES_ETAPES[e] for e in chaine.ETAPES)
             + " | Distance |")
    out.append("|---|---|" + "---|" * len(chaine.ETAPES) + "---:|")
    for o in r.opportunites:
        e = r.etats[o.id]
        out.append(f"| **{o.nom}** (`{o.id}`, {o.module}) | {o.statut_mere} | "
                 + " | ".join(e[x][0] for x in chaine.ETAPES) + f" | {chaine.distance(e)} |")
    out.append("\nDétail des étapes :\n")
    for o in r.opportunites:
        e = r.etats[o.id]
        out.append(f"- `{o.id}` : " + " · ".join(f"{chaine.LIBELLES_ETAPES[x]} : {e[x][1]}" for x in chaine.ETAPES))

    out.append("\n## Priorités vers le premier euro\n")
    out.append("Ordre : opportunités actives avant les tests en attente de verdict, puis distance à l'argent, "
             "échéance la plus proche, score prouvé (seules les notes mesurées comptent).\n")
    for i, o in enumerate(r.priorites, 1):
        out.append(f"{i}. **{o.nom}** : distance {chaine.distance(r.etats[o.id])}, score prouvé {o.score_prouve}/30, "
                 f"score avec hypothèses {o.score_total}/30, confiance {round(o.confiance * 100)} %. "
                 f"Prochaine action : {o.prochaine_action} (responsable : {o.responsable}).")
    hors = [o for o in r.opportunites if o.statut_mere not in ("actif", "test")]
    if hors:
        out.append("\nHors priorité (gelé ou arrêté par la mère) : "
                 + ", ".join(f"{o.nom} ({o.statut_mere})" for o in hors) + ".")

    out.append("\n## Les six critères de chaque opportunité\n")
    out.append("Nature : m = mesuré (source citée), c = calcul, h = hypothèse.\n")
    out.append("| Opportunité | " + " | ".join(LIBELLES_CRITERES[k] for k in CRITERES) + " | Prouvé | Total |")
    out.append("|---|" + "---|" * len(CRITERES) + "---:|---:|")
    abrev = {"mesuré": "m", "calcul": "c", "hypothèse": "h"}
    for o in r.opportunites:
        cells = [f"{o.notes[k].note} {abrev[o.notes[k].nature]}" if k in o.notes else "—" for k in CRITERES]
        out.append(f"| {o.nom} | " + " | ".join(cells) + f" | {o.score_prouve} | {o.score_total} |")

    out.append("\n## Critères d'arrêt et verdicts\n")
    out.append("| Opportunité | Critère | Date | Mesure | Statut | Détail | Si échec |")
    out.append("|---|---|---|---:|---|---|---|")
    for o in r.opportunites:
        for a in r.arrets[o.id]:
            mesure = "—" if a.mesure is None else (
                euros(a.mesure) if prive and INDICATEURS.get(a.indicateur, ("", ""))[1] == "centimes" else
                ("[privé]" if INDICATEURS.get(a.indicateur, ("", ""))[1] == "centimes" else f"{a.mesure:g}"
                 if isinstance(a.mesure, (int, float)) else str(a.mesure)))
            seuil = f" (seuil {'≥' if a.sens == 'min' else '≤'} {a.seuil:g})" if a.indicateur != "prévision" else ""
            out.append(f"| {o.id} | {a.libelle}{seuil} | {a.date} | {mesure} | {a.statut} | {a.detail} | "
                     f"{a.si_echec} |")

    out.append("\n## Conflits à résoudre\n")
    out.extend(f"- CONFLIT : {x}" for x in r.conflits) if r.conflits else out.append("Aucun.")
    out.append("\n## Alertes\n")
    out.extend(f"- {x}" for x in r.alertes) if r.alertes else out.append("Aucune.")
    if r.declares:
        out.append("\nStatuts déclarés par les registres des modules : "
                 + ", ".join(f"`{k}` : {v}" for k, v in sorted(r.declares.items())) + ".")

    if prive:
        out.append("\n## Montants par opportunité (privé)\n")
        out.append("| Opportunité | Encaissé net | Remboursé | Coûts | Bénéfice net | Ventes | Échecs de paiement |")
        out.append("|---|---:|---:|---:|---:|---:|---|")
        for cle in [TOUTE_L_ENTREPRISE, *[o.id for o in r.opportunites], stripe.NON_ATTRIBUE]:
            def g(ind: str, cle: str = cle) -> chaine.Valeur:
                return chaine.lire(c, cle, ind)
            if cle == stripe.NON_ATTRIBUE and g("encaisse_net").valeur is None:
                continue
            ech = g("paiements_echoues")
            out.append(f"| {cle} | {euros(g('encaisse_net').valeur)} | {euros(g('remboursements').valeur)} | "
                     f"{euros(g('couts').valeur)} | {euros(g('benefice_net').valeur)} | {g('ventes_payees').valeur} | "
                     f"{ech.valeur} {_note(ech.faits)} |")

    out.append("\n## Sources lues dans ce passage\n")
    out.append("| Source | État | Détail |")
    out.append("|---|---|---|")
    out.extend(f"| {a} | {b} | {d} |" for a, b, d in r.sources_lues)
    if r.erreurs:
        out.append("\n## Erreurs de lecture (rejetées, jamais corrigées en silence)\n")
        out.extend(f"- {e}" for e in r.erreurs)
    return "\n".join(out) + "\n"


def faits_publics(r: Rapport) -> list[dict[str, Any]]:
    """Le contrat partagé : les faits non privés, que tout module peut lire sans dépendre de ce code."""
    return [f.to_dict() for f in r.faits if not f.prive]


def statut_global(r: Rapport) -> str:
    return combiner(r.etats[o.id]["encaisse"][0] for o in r.priorites) if r.priorites else INCONNU


__all__ = ["Rapport", "construire", "rendre", "faits_publics", "euros", "statut_global", "ECHEC"]
