"""Assemblage du rapport de l'entreprise mère et rendu du tableau de bord commercial (public et privé)."""

from __future__ import annotations

import json
import tomllib
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from . import chaine, controles, sources, stripe
from .faits import INDICATEURS, TOUTE_L_ENTREPRISE, Fait
from .portefeuille import CRITERES, LIBELLES_CRITERES, Opportunite, charger
from .statuts import CONFLIT, ECHEC, INCONNU, PROUVE, combiner

INDICATEURS_OBLIGATOIRES = ("visiteurs", "prospects_contactes", "prospects_reels", "envois_bloques", "reponses",
                            "prospects_qualifies", "qualifies_verifies", "conversions", "ventes_payees",
                            "paiements_echoues", "remboursements", "litiges_ouverts", "couts", "frais_paiement",
                            "benefice_net", "ca_annonce", "encaisse_net", "verse_en_banque", "credite_en_banque",
                            "abonnements_actifs", "offres_actives")
LIBELLES = {"visiteurs": "Visiteurs", "prospects_contactes": "Prospects contactés",
            "envois_bloques": "Envois bloqués par un filtre", "reponses": "Réponses",
            "prospects_qualifies": "Prospects qualifiés", "conversions": "Conversions (proposition acceptée)",
            "ventes_payees": "Ventes payées", "paiements_echoues": "Paiements échoués",
            "remboursements": "Remboursements", "couts": "Coûts directs", "frais_paiement": "Frais de paiement",
            "benefice_net": "Bénéfice net (hors temps)", "ca_annonce": "CA annoncé (factures non payées)",
            "encaisse_net": "Argent encaissé net", "abonnements_actifs": "Abonnements actifs",
            "offres_actives": "Offres avec un prix actif", "heures": "Heures du fondateur",
            "prospects_reels": "Prospects réels (vérifiés par le web public)",
            "qualifies_verifies": "Qualifiés et vérifiés réels", "litiges_ouverts": "Litiges de paiement ouverts",
            "verse_en_banque": "Versé vers la banque (selon le prestataire)",
            "credite_en_banque": "Crédité en banque (vérifié sur le relevé)"}


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
    controles: list[controles.Controle] = field(default_factory=list)
    rejeux_a_ecrire: list[dict[str, Any]] | None = None  # écrits par l'appelant après la garde
    controles_a_ecrire: list[controles.Controle] | None = None


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
               client: stripe.ClientLecture | None = None, controler: bool = False,
               lire_url: Callable[[str], tuple[int, str]] | None = None) -> Rapport:
    """Lit toutes les sources, consolide, fait contrôler chaque affirmation par un autre acteur que son
    producteur, évalue la chaîne. N'écrit que les instantanés (privés ou publics sans fuite) et les rejeux."""
    erreurs: list[str] = []
    alertes: list[str] = []
    lues: list[tuple[str, str, str]] = []
    ctrls: list[controles.Controle] = []
    lecteur_url = lire_url or controles.lire_url
    config = tomllib.loads((racine / "donnees/sources.toml").read_text(encoding="utf-8"))
    opportunites, reglages, err = charger(racine / "donnees/portefeuille.toml")
    erreurs += err
    depots = {nom: _resoudre(racine, cands) for nom, cands in config.get("depots", {}).items()}
    for nom, chemin in depots.items():
        lues.append((f"dépôt {nom}", "trouvé" if chemin else "absent", ""))
    fichiers = {k: _fichier(racine, depots, v) for k, v in config.get("fichiers", {}).items()}
    faits: list[Fait] = []
    ids = [o.id for o in opportunites]
    etat_ctrl, prive_ctrl = racine / "etat/controles.json", racine / "prive/controles_prospects.json"

    # Amélioration continue : prévisions et verdicts du poste business.
    rejetees_prev: list[str] = []
    previsions = sources.lire_previsions(fichiers.get("previsions"), erreurs, rejetees_prev)
    lues.append(("prévisions (poste business)", "lu" if previsions is not None else "illisible",
                 f"{len(previsions or [])} prévision(s)"))
    rattachement = {pid: o.id for o in opportunites for pid in o.previsions}
    faits += sources.faits_verdicts(previsions, rattachement, jour, "memoire/PREDICTIONS.csv (poste business)",
                                    rejetees_prev)

    # Citations : chaque note « mesuré » est confirmée par sa source (page publique ou données brutes).
    anciens = {c.id: c for c in controles.relire(etat_ctrl, ("citation:",))}
    tiers = tuple(str(t) for t in reglages.get("sources_tierces", []))
    for o in opportunites:
        for k, note in o.notes.items():
            if note.nature != "mesuré":
                continue
            cid = f"citation:{o.id}/{k}"
            if note.verif is None:
                c = controles.controler_citation(o.id, k, {}, depots)
            elif controler:
                c = controles.controler_citation(o.id, k, note.verif, depots, lecteur_url, tiers)
            else:
                c = anciens.get(cid)
                # Un contrôle relu ne vaut que pour la même façon de vérifier, et il n'est jamais PROUVÉ.
                if c is not None and not c.reference.endswith(f"signature {controles.signature(note.verif)}"):
                    c = None
                c = c or controles.Controle(
                    cid, f"La source de la note « {k} » de {o.id} dit ce que la note affirme", "portefeuille",
                    "page-publique" if "url" in note.verif else "donnees", "non relancé", INCONNU,
                    "relancer avec --controler (note modifiée ou jamais contrôlée)", "", opportunite=o.id)
            ctrls.append(c)
            if c.statut == PROUVE:
                o.notes_verifiees.add(k)

    # Acheteurs : pipeline privé ; chaque prospect contacté est vérifié par le web public.
    evenements, err = sources.lire_pipeline(fichiers.get("pipeline"))
    erreurs += err
    lues.append(("pipeline commercial (privé)", "lu" if evenements is not None else "absent",
                 f"{len(evenements or [])} événement(s)"))
    rejetees = len(err)
    faits += sources.faits_pipeline(evenements, ids, "prive/pipeline.csv", rejetees)
    domaines = {(e.opportunite, e.ref): e.domaine for e in evenements or [] if e.domaine}
    prospects = controles.prospects_contactes(evenements, domaines)
    recompte = racine / "prive/recomptage_messagerie.json"
    rc = json.loads(recompte.read_text(encoding="utf-8")) if recompte.is_file() else None
    # Aucun fichier ne rend un relevé opposable, quel que soit son contenu : seule une lecture de la messagerie faite
    # par la mère elle-même, en mémoire, dans ce passage, le pourrait. Elle n'existe pas encore (PLAN, geste 10).
    opposable = False
    # 7 : les domaines du second relevé valent pour leur opportunité seulement.
    vus_messagerie = ({str(o): {str(d).lower() for d in liste} for o, liste in (rc.get("domaines") or {}).items()}
                      if rc and rc.get("domaines") else None)
    if controler:
        ctrl_prospects = [controles.controler_prospect(p, lecteur_url, None if vus_messagerie is None else
                                                       vus_messagerie.get(p.opportunite, set()), opposable)
                          for p in prospects]
        controles.instantane(ctrl_prospects, prive_ctrl)
    else:
        ctrl_prospects = controles.relire(prive_ctrl, ("prospect:",))
    # Clés (opportunité, référence) : un prospect qualifié ailleurs ne qualifie jamais cette opportunité.
    reels = {(c.opportunite, c.id.split(":", 2)[2]) for c in ctrl_prospects if c.statut == PROUVE}
    tranches = {(c.opportunite, c.id.split(":", 2)[2]) for c in ctrl_prospects if c.statut in (PROUVE, ECHEC)}
    qualifies = {(e.opportunite, e.ref) for e in evenements or [] if e.etape in sources.QUALIFIE and e.preuve}
    for cle in [TOUTE_L_ENTREPRISE, *ids]:
        siens = [p for p in prospects if cle in (TOUTE_L_ENTREPRISE, p.opportunite)]
        if evenements is None:
            faits.append(Fait("web-public", "prospects_reels", None, INCONNU, "contrôle des prospects", cle))
            continue
        cles_siennes = {(p.opportunite, p.ref) for p in siens}
        n_reels = len(cles_siennes & reels)
        indecis = cles_siennes - tranches
        # Un compte n'est PROUVÉ que si chaque prospect a un contrôle tranché ; sinon ce n'est qu'un minimum.
        if indecis or rejetees:
            faits.append(Fait("web-public", "prospects_reels", None, INCONNU, "contrôle des prospects", cle,
                              jour.isoformat(), note=f"au moins {n_reels} ; {len(indecis)} prospect(s) sans contrôle "
                              "tranché" + (" ; lignes de pipeline rejetées" if rejetees else "")))
        else:
            faits.append(Fait("web-public", "prospects_reels", n_reels, PROUVE, "contrôle des prospects (absence de "
                              "rebond, site joignable)", cle, jour.isoformat(),
                              f"{len(cles_siennes)} prospect(s) contrôlé(s) par le web public"))
        qualifies_siens = {k for k in qualifies if cle in (TOUTE_L_ENTREPRISE, k[0])}
        n_q = len(qualifies_siens & reels)
        if (qualifies_siens - tranches) or rejetees:
            faits.append(Fait("web-public", "qualifies_verifies", None, INCONNU, "qualifiés et vérifiés réels", cle,
                              jour.isoformat(), note=f"au moins {n_q} ; qualifiés sans contrôle tranché"))
        else:
            faits.append(Fait("web-public", "qualifies_verifies", n_q, PROUVE, "qualifiés et vérifiés réels", cle,
                              jour.isoformat(), f"{len(qualifies_siens)} qualifié(s), tous contrôlés"))
    for opp in sorted({p.opportunite for p in prospects}):
        liste = [c for c in ctrl_prospects if c.opportunite == opp]
        statut = combiner(c.statut for c in liste) if liste else INCONNU
        detail = ", ".join(f"{n} {s}" for s, n in sorted(Counter(c.statut for c in liste).items())) or "non lancé"
        ctrls.append(controles.Controle(f"prospects:{opp}", f"Les prospects contactés pour {opp} existent",
                                        "pipeline", "web-public", "absence de rebond et site du domaine joignable",
                                        statut, detail, jour.isoformat(), "détail en privé", opportunite=opp))
    faits.append(Fait("compteur", "visiteurs", None, INCONNU, "aucun compteur de visites activé",
                      note="à activer sur les pages d'offre avant toute campagne"))

    # Recomptage indépendant de la messagerie (un second lecteur, pas l'agent qui a rempli le pipeline).
    lecteur = str((rc or {}).get("lecteur", "recomptage-independant"))
    # Le second relevé arrive comme un fichier : la mère ne lit pas la messagerie elle-même. Il peut révéler un écart
    # (CONFLIT), jamais prouver ; seule une lecture directe par la mère, dans ce passage, le rendrait opposable.
    if rc is not None and controles._racine(lecteur) == "pipeline":
        ctrls.append(controles.Controle("pipeline:recomptage", "Le pipeline contient tous les envois de la messagerie",
                                        "pipeline", "recomptage-independant", "second relevé de la messagerie", ECHEC,
                                        "le second relevé se déclare fait par le pipeline lui-même : auto-validation "
                                        "refusée", str(rc.get("date", ""))))
    elif rc is not None and evenements is not None:
        pipeline_envois = Counter(p.opportunite for p in prospects)
        ecarts = {k: (rc.get("envois", {}).get(k, 0), pipeline_envois.get(k, 0))
                  for k in set(rc.get("envois", {})) | set(pipeline_envois)
                  if rc.get("envois", {}).get(k, 0) != pipeline_envois.get(k, 0)}
        # Réponses, rebonds et défis anti-spam se comptent aussi : un rebond manqué fausse les prospects réels.
        for cle_rc, etapes in (("reponses", sources.REPONDU), ("rebonds", {"rebond"}), ("defis_antispam", {"bloque"})):
            vus = len({(e.opportunite, e.ref) for e in evenements if e.etape in etapes})
            if int(rc.get(cle_rc, 0)) != vus:
                ecarts[cle_rc] = (int(rc.get(cle_rc, 0)), vus)
        ctrls.append(controles.Controle(
            "pipeline:recomptage", "Le pipeline contient tous les envois, réponses et rebonds de la messagerie",
            "pipeline", lecteur,
            "second relevé de la messagerie par un autre lecteur",
            CONFLIT if ecarts else (PROUVE if opposable else INCONNU),
            "écarts (second relevé, pipeline) : " + ", ".join(f"{k} {v}" for k, v in sorted(ecarts.items()))
            if ecarts else ("envois, réponses, rebonds et défis concordants" + ("" if opposable else
                            " ; relevé fourni hors de la mère : non opposable")), str(rc.get("date", ""))))
    else:
        ctrls.append(controles.Controle("pipeline:recomptage", "Le pipeline contient tous les envois de la messagerie",
                                        "pipeline", "recomptage-independant", "second relevé de la messagerie", INCONNU,
                                        "aucun second relevé", jour.isoformat()))

    # Coûts.
    couts, err = sources.lire_couts(fichiers.get("couts"), "prive/couts.csv")
    erreurs += err
    faits += couts
    lues.append(("journal des coûts (privé)", "lu" if couts and couts[0].statut != INCONNU else "absent", ""))

    # Argent : le prestataire en lecture seule, puis son grand livre, puis la banque.
    instantane = racine / "prive/stripe.json"
    correspondances = {o.id: o.stripe_produits for o in opportunites if o.stripe_produits}
    encaissements: list[tuple[str, int, str]] | None = None
    virements: list[dict[str, Any]] | None = None
    grand_livre: dict[str, Any] = {}
    if lire_stripe:
        r = stripe.releve(client or stripe.ClientLecture(), correspondances, str(reglages.get("devise", "eur")),
                          opportunites=ids)
        erreurs += [f"stripe : {e}" for e in r.erreurs]
        stripe_faits, encaissements, virements, grand_livre = r.faits, r.encaissements, r.virements, r.grand_livre
        if not any(f.indicateur == "encaisse_net" and f.opportunite == TOUTE_L_ENTREPRISE and f.valeur is None
                   for f in r.faits):
            instantane.parent.mkdir(exist_ok=True)
            instantane.write_text(json.dumps({"faits": [f.to_dict() for f in r.faits], "encaissements":
                                              r.encaissements, "virements": r.virements, "grand_livre": r.grand_livre},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
        lues.append(("prestataire de paiement", "lu en direct" if not r.erreurs else "lu en partie",
                     f"{len(r.erreurs)} lecture(s) refusée(s)" if r.erreurs else ""))
    elif instantane.is_file():
        # L'instantané est la mémoire de la mère : relu pour mémoire, jamais PROUVÉ (seul --stripe relit la source).
        brut = json.loads(instantane.read_text(encoding="utf-8"))
        quand = str(brut["faits"][0].get("date", "?"))[:10] if brut.get("faits") else "?"
        stripe_faits = [Fait(**{**f, "statut": INCONNU, "valeur": None, "preuve": "",
                                "note": f"relevé du {quand}, non relu dans ce passage"}) for f in brut["faits"]]
        encaissements, virements, grand_livre = None, None, {}
        lues.append(("prestataire de paiement", f"non relu (dernier relevé privé du {quand})",
                     "relancer avec --stripe"))
    else:
        stripe_faits = [Fait("stripe", "encaisse_net", None, INCONNU, "prestataire non relu", prive=True),
                        Fait("stripe", "ventes_payees", None, INCONNU, "prestataire non relu")]
        lues.append(("prestataire de paiement", "non relu", "relancer avec --stripe"))
    faits += stripe_faits
    if grand_livre.get("lu"):
        ecarts = grand_livre.get("ecarts") or []
        ctrls.append(controles.Controle(
            "argent:grand-livre", "Chaque paiement réussi figure au grand livre du prestataire, même montant",
            "mere:releve-paiements", "stripe:grand-livre",
            "contrôle croisé /v1/charges contre /v1/balance_transactions",
            CONFLIT if ecarts else PROUVE, "; ".join(ecarts) or f"{grand_livre.get('verifies', 0)} paiement(s) "
            "réussi(s) rapproché(s)", jour.isoformat()))
    else:
        ctrls.append(controles.Controle("argent:grand-livre", "Chaque paiement réussi figure au grand livre",
                                        "mere:releve-paiements", "stripe:grand-livre", "contrôle croisé", INCONNU,
                                        "grand livre non lu", jour.isoformat()))
    releve_banque, err = controles.lire_releve_bancaire(racine / "prive/banque.csv")
    erreurs += err
    if virements is None:
        banque = controles.Controle("argent:credite-en-banque", "L'argent versé est crédité en banque", "stripe",
                                    "banque", "rapprochement", INCONNU, "virements non lus", jour.isoformat())
    else:
        banque = controles.rapprocher_virements(virements, releve_banque, jour)
    ctrls.append(banque)
    verse = sum(int(v.get("amount") or 0) for v in virements or [] if v.get("status") == "paid" and v.get("livemode"))
    faits.append(Fait("banque", "credite_en_banque", verse if banque.statut == PROUVE else None, banque.statut,
                      "relevé bancaire du propriétaire rapproché des virements", TOUTE_L_ENTREPRISE, jour.isoformat(),
                      banque.detail if banque.statut == PROUVE else "", note="" if banque.statut == PROUVE
                      else banque.detail, prive=True))

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

    # Suites de tests : rejouées deux fois dans un clone propre du commit, par la mère (pas par le module).
    etat_rejeux = racine / "etat/rejeux.json"
    if rejouer:
        resultats = [controles.rejouer_propre(r["nom"], depots.get(r["depot"]), list(r["commande"]), r["bilan"],
                                              delai=int(r.get("delai", 900))) for r in config.get("rejeu", [])]
    else:
        resultats = json.loads(etat_rejeux.read_text(encoding="utf-8")) if etat_rejeux.is_file() else []
    depots_rejeux = {r["nom"]: depots.get(r["depot"]) for r in config.get("rejeu", [])}
    ctrl_suites = [controles.controle_suite(r, depots_rejeux.get(r["nom"]), ce_passage=rejouer) for r in resultats]
    ctrls += ctrl_suites
    rattach_rejeux: dict[str, list[str]] = {}
    for o in opportunites:
        if o.rejeu:
            rattach_rejeux.setdefault(o.rejeu, []).append(o.id)
    faits += sources.faits_rejeux(ctrl_suites, rattach_rejeux)
    lues.append(("suites de tests", "rejouées en clone propre" if rejouer else "dernier état",
                 f"{len(resultats)} suite(s)"))

    # La mère elle-même : contrôlée par NOVARYS Ω, jamais par elle-même.
    head_mere = sources._git(racine, "rev-parse", "HEAD")
    preuves = (depots.get("novarys") / "registre/preuves.jsonl") if depots.get("novarys") else None
    ctrls += controles.controle_par_novarys(preuves, "mere-", head_mere, racine)

    # Rapprochement : ce que les modules déclarent contre ce que la source qui fait foi montre.
    declarations: list[sources.Declaration] = []
    for cle, lecteur in (("tableau_novarys", sources.declarations_novarys), ("kpi_velyx", sources.declarations_velyx)):
        decl, err = lecteur(fichiers.get(cle))
        declarations += decl
        erreurs += [f"{cle} : {e}" for e in err]
        lues.append((cle.replace("_", " "), "lu" if decl else "absent ou vide", f"{len(err)} erreur(s)" if err else ""))
    modules = {o.id: o.module for o in opportunites}
    controle_faits, al = chaine.rapprocher(declarations, encaissements, evenements, modules)
    faits += controle_faits
    alertes += al
    conflits = [f.note for f in controle_faits if f.statut == CONFLIT]
    for d in declarations:
        faux = [f for f in controle_faits
                if f.opportunite == f"declaration:{d.module}" and f.indicateur == d.indicateur]
        retard = [a for a in al if d.indicateur == "prospects_contactes"
                  and a.startswith(f"registre de {d.module} en retard")]
        statut = CONFLIT if faux else (INCONNU if retard or (d.indicateur == "encaisse_net" and encaissements is None)
                                       else PROUVE)
        ctrls.append(controles.Controle(
            f"declaration:{d.module}:{d.indicateur}", f"Ce que {d.module} déclare ({d.indicateur}) est vrai à sa date",
            d.module, "stripe" if d.indicateur == "encaisse_net" else "pipeline",
            "rapprochement à la même date avec la source qui fait foi", statut,
            faux[0].note if faux else (retard[0] if retard else "concordant à la date de la déclaration"),
            d.date, d.source))

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
        ctrls.append(controles.Controle(
            f"statut:{o.id}", f"Le registre de {o.declare.get('depot')} décrit {o.id} comme il est", o.declare.get(
                "depot", "registre"), "pipeline", "statut déclaré contre envois des 14 derniers jours",
            CONFLIT if conflit else (PROUVE if evenements is not None else INCONNU),
            conflit or f"déclaré « {declares[o.id]} », {activite.get(o.id, 0)} envoi(s) récent(s)", jour.isoformat(),
            str(o.declare.get("fichier", "")), opportunite=o.id))
    for o in opportunites:
        if o.statut_mere in ("actif", "test") and not activite.get(o.id) and evenements is not None:
            alertes.append(f"{o.id} : active, mais aucun envoi ces 14 derniers jours")
        if o.statut_mere in ("gele", "arrete") and activite.get(o.id):
            alertes.append(f"{o.id} : {o.statut_mere} pour la mère, {activite[o.id]} envoi(s) récent(s) : "
                           f"répondre aux retours, ne plus relancer")

    consolide = chaine.consolider(faits)
    index = {c.id: (c.statut, c.detail) for c in ctrls}
    regles = {"prospects_contactes": {"envoi", "relance"}, "envois_bloques": {"bloque"}, "reponses": sources.REPONDU,
              "prospects_qualifies": sources.QUALIFIE, "conversions": {"gagne"}}

    def mesure_a_date(opp: str, indicateur: str, limite: date) -> tuple[int | float, str] | None:
        """Valeur d'un indicateur telle qu'elle était à la fin du jour `limite` (événements datés seulement)."""
        if indicateur in regles:
            if evenements is None or rejetees:
                return None
            lignes = [e for e in evenements if e.opportunite == opp and e.etape in regles[indicateur]
                      and (sources.jour_de(e.date) or date.max) <= limite]
            return len({e.ref for e in lignes}), PROUVE if all(e.preuve for e in lignes) else INCONNU
        if indicateur in ("ventes_payees", "encaisse_net"):
            actuel = chaine.lire(consolide, opp, indicateur)
            if encaissements is None or actuel.statut != PROUVE:
                return None
            dates = [(n, sources.jour_de(q) or date.max) for q, n, o in encaissements if o == opp and n > 0]
            if indicateur == "ventes_payees":
                return sum(1 for _, j in dates if j <= limite), PROUVE
            return sum(n for n, j in dates if j <= limite), PROUVE
        return None

    arrets = {o.id: chaine.evaluer_arrets(o, consolide, jour, previsions, mesure_a_date) for o in opportunites}
    # Amélioration : un verdict saisi par l'auteur n'est PROUVÉ que s'il concorde avec une mesure de source externe
    # (prestataire de paiement, banque), relue dans ce passage. Un compte du pipeline, écrit lui aussi par l'auteur,
    # ne confirme rien.
    externes = {"ventes_payees", "encaisse_net", "credite_en_banque", "abonnements_actifs", "remboursements",
                "paiements_echoues", "offres_actives"}
    a_mesurer = {str(k): str(v) for k, v in (reglages.get("indicateurs_previsions") or {}).items()}
    for p in previsions or []:
        if p.reel is None or not p.date_verdict:
            continue
        opp = rattachement.get(p.id, TOUTE_L_ENTREPRISE)
        ind = a_mesurer.get(p.id)
        if ind is None:
            statut, detail = INCONNU, "verdict saisi par l'auteur, sans indicateur pour le confirmer"
        elif ind not in externes:
            statut, detail = INCONNU, f"{ind} est écrit par l'auteur du pipeline : il ne peut pas confirmer un verdict"
        else:
            m = mesure_a_date(opp, ind, date.fromisoformat(p.date_verdict)) if opp != TOUTE_L_ENTREPRISE else None
            v = chaine.lire(consolide, opp, ind) if m is None else chaine.Valeur(m[0], m[1])
            if v.statut != PROUVE or not isinstance(v.valeur, (int, float)):
                statut, detail = INCONNU, f"{ind} non prouvé dans ce passage"
            elif float(v.valeur) == p.reel:
                statut, detail = PROUVE, f"{ind} = {v.valeur:g}, comme le verdict saisi"
            else:
                statut, detail = CONFLIT, f"le verdict saisi dit {p.reel:g}, la mesure ({ind}) dit {v.valeur:g}"
        ctrls.append(controles.Controle(f"verdict:{p.id}", f"Le résultat saisi pour {p.id} est le résultat mesuré",
                                        "strat-ge-business", "mere:mesure", "verdict saisi contre la mesure à sa date",
                                        statut, detail, jour.isoformat(), "memoire/PREDICTIONS.csv", opportunite=opp))
    index = {c.id: (c.statut, c.detail) for c in ctrls}
    etats = {o.id: chaine.etats_chaine(o, consolide, arrets[o.id], index) for o in opportunites}
    for o in opportunites:
        for a in arrets[o.id]:
            if a.detail == "verdict dû sans mesure":
                alertes.append(f"{o.id} : verdict dû sans mesure ({a.libelle})")
    for c in ctrls:
        if c.statut == CONFLIT and c.id.startswith(("argent:", "suite:", "citation:", "pipeline:", "novarys:")):
            conflits.append(f"{c.objet} : {c.detail}")
    # Rien de public n'est écrit ici : l'appelant écrit rejeux et contrôles seulement après la garde.
    publics_ctrl = [c for c in ctrls if not c.id.startswith("prospect:")]
    prio = chaine.priorites([(o, etats[o.id]) for o in opportunites])
    publics = {str(m) for m in reglages.get("montants_publics", [])}
    return Rapport(jour, datetime.now(UTC).isoformat(timespec="minutes"), opportunites, faits, consolide, etats,
                   arrets, prio, conflits, alertes, lues, erreurs, declares, publics, ctrls,
                   resultats if rejouer else None, publics_ctrl if (controler or rejouer or lire_stripe) else None)


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
    credite = chaine.lire(c, TOUTE_L_ENTREPRISE, "credite_en_banque")
    ctrl = {x.id: x for x in r.controles}
    banque = ctrl.get("argent:credite-en-banque")
    livre = ctrl.get("argent:grand-livre")
    if enc.statut == PROUVE and enc.valeur == 0:
        verdict = "non atteint (PROUVÉ : aucun paiement réussi chez le prestataire)"
    elif (credite.statut == PROUVE and isinstance(credite.valeur, int) and credite.valeur > 0 and banque
          and banque.statut == PROUVE):
        verdict = "atteint (PROUVÉ : crédité en banque, vérifié sur le relevé)"
    elif enc.statut == PROUVE:
        verdict = "INCONNU : paiement réussi, mais crédit en banque non vérifié"
    else:
        verdict = f"{enc.statut} : l'argent n'a pas pu être relu dans ce passage"
    out.append(f"**Premier euro : {verdict}**{' (' + euros(enc.valeur) + ')' if prive and enc.valeur else ''}. "
               f"Conflits ouverts : {len(r.conflits)}. Alertes : {len(r.alertes)}.")
    ventes = chaine.lire(c, TOUTE_L_ENTREPRISE, "ventes_payees").valeur
    out.append(f"\nNiveaux de l'argent : paiement réussi → {ventes} "
               f"vente(s) · rapprochement grand livre → {livre.statut if livre else INCONNU} · versé vers la banque → "
               f"{chaine.lire(c, TOUTE_L_ENTREPRISE, 'verse_en_banque').statut} · crédité en banque → "
               f"{banque.statut if banque else INCONNU} ({banque.detail if banque else 'non contrôlé'}).")

    def compte(prefixe: str) -> str:
        liste = [x for x in r.controles if x.id.startswith(prefixe)]
        ok = sum(1 for x in liste if x.statut == PROUVE)
        return f"{ok}/{len(liste)}"

    def val(ind: str) -> str:
        v = chaine.lire(c, TOUTE_L_ENTREPRISE, ind)
        return f"{_valeur(v, ind, prive)} ({v.statut})"

    novarys = [x for x in r.controles if x.id.startswith("novarys:")]
    out.append("\n## Trois réussites à ne pas confondre\n")
    out.append("Seule la réussite commerciale fait avancer une opportunité vers l'argent. L'activité ne prouve rien ; "
               "la réussite technique prouve qu'un outil marche, pas qu'il se vend.\n")
    out.append("| Niveau | Mesure | Valeur |")
    out.append("|---|---|---|")
    out.append(f"| Activité | Prospects contactés | {val('prospects_contactes')} |")
    out.append(f"| Activité | Offres avec un prix actif | {val('offres_actives')} |")
    out.append(f"| Activité | Contrôles exécutés dans ce passage | {len(r.controles)} |")
    out.append(f"| Technique | Suites rejouées deux fois en clone propre et vertes | {compte('suite:')} |")
    out.append(f"| Technique | Notes « mesuré » dont la source est confirmée | {compte('citation:')} |")
    out.append(f"| Technique | La mère contrôlée par NOVARYS Ω | "
               f"{combiner(x.statut for x in novarys) if novarys else INCONNU} |")
    out.append(f"| Commercial | Prospects réels vérifiés | {val('prospects_reels')} |")
    out.append(f"| Commercial | Réponses | {val('reponses')} |")
    out.append(f"| Commercial | Qualifiés et vérifiés réels | {val('qualifies_verifies')} |")
    out.append(f"| Commercial | Ventes payées | {val('ventes_payees')} |")
    out.append(f"| Commercial | Crédité en banque | {val('credite_en_banque')} |")

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

    out.append("\n## Contrôles indépendants de ce passage\n")
    out.append("Aucun producteur ne se contrôle lui-même : chaque ligne nomme qui affirme et qui vérifie.\n")
    out.append("| Contrôle | Producteur → contrôleur | Méthode | Statut | Détail |")
    out.append("|---|---|---|---|---|")
    for x in r.controles:
        if x.id.startswith("prospect:") and not prive:
            continue
        out.append(f"| {x.objet} | {x.producteur} → {x.controleur} | {x.methode} | {x.statut} | {x.detail} |")

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
        if prive:
            out.extend(f"- {e}" for e in r.erreurs)
        else:
            out.append(f"{len(r.erreurs)} erreur(s) de lecture : le détail est dans le tableau privé.")
    return "\n".join(out) + "\n"


def faits_publics(r: Rapport) -> list[dict[str, Any]]:
    """Le contrat partagé : les faits non privés, que tout module peut lire sans dépendre de ce code."""
    return [f.to_dict() for f in r.faits if not f.prive]


def statut_global(r: Rapport) -> str:
    return combiner(r.etats[o.id]["encaisse"][0] for o in r.priorites) if r.priorites else INCONNU


__all__ = ["Rapport", "construire", "rendre", "faits_publics", "euros", "statut_global", "ECHEC"]
