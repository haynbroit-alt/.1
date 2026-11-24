"""La chaîne opportunité → produit → offre → acheteur → vente → encaissé → amélioration → croissance.

Consolidation des faits, rapprochement des déclarations avec l'argent réellement encaissé, état de chaque
étape, critères d'arrêt et priorité. Rien ici ne lit le réseau : tout part des faits déjà relevés.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from .faits import INDICATEURS, Fait
from .portefeuille import Opportunite
from .sources import Declaration, Evenement, Prevision
from .statuts import CONFLIT, ECHEC, INCONNU, PROUVE, combiner

ETAPES = ("opportunite", "produit", "offre", "acheteur", "vente", "encaisse", "amelioration", "croissance")
LIBELLES_ETAPES = {"opportunite": "Opportunité", "produit": "Produit", "offre": "Offre", "acheteur": "Acheteur",
                   "vente": "Vente", "encaisse": "Encaissé", "amelioration": "Amélioration",
                   "croissance": "Croissance"}
JUSQU_A_L_ARGENT = ETAPES[:6]


@dataclass
class Valeur:
    """Valeur consolidée d'un indicateur pour une opportunité."""

    valeur: int | float | str | bool | None
    statut: str
    faits: list[Fait] = field(default_factory=list)

    @property
    def sources(self) -> list[str]:
        return sorted({f.module for f in self.faits})


Consolide = dict[tuple[str, str], Valeur]


def consolider(faits: list[Fait]) -> Consolide:
    """Une valeur par (opportunité, indicateur). Deux sources PROUVÉES qui divergent donnent un CONFLIT ;
    un fait CONFLIT (rapprochement raté) contamine l'indicateur."""
    groupes: dict[tuple[str, str], list[Fait]] = defaultdict(list)
    for f in faits:
        groupes[(f.opportunite, f.indicateur)].append(f)
    sortie: Consolide = {}
    for cle, liste in groupes.items():
        prouves = [f for f in liste if f.statut in (PROUVE, ECHEC) and f.valeur is not None]
        if any(f.statut == CONFLIT for f in liste):
            sortie[cle] = Valeur(None, CONFLIT, liste)
        elif len({f.valeur for f in prouves}) > 1:
            sortie[cle] = Valeur(None, CONFLIT, liste)
        elif prouves:
            sortie[cle] = Valeur(prouves[0].valeur, combiner(f.statut for f in prouves), liste)
        else:
            sortie[cle] = Valeur(None, INCONNU, liste)
    return sortie


def lire(c: Consolide, opp: str, indicateur: str) -> Valeur:
    return c.get((opp, indicateur)) or Valeur(None, INCONNU)


def _avant(evenement: str, declaration: str) -> bool | None:
    """L'événement précède-t-il la déclaration ? None si on ne peut pas le dire (même jour sans heure)."""
    if not declaration:
        return None
    if len(evenement) <= 10 and len(declaration) > 10 and evenement[:10] == declaration[:10]:
        return None
    return evenement <= declaration if len(declaration) > 10 else evenement[:10] <= declaration[:10]


def rapprocher(declarations: list[Declaration], encaissements: list[tuple[str, int, str]] | None,
               evenements: list[Evenement] | None, modules: dict[str, str]
               ) -> tuple[list[Fait], list[str]]:
    """Compare ce que chaque module déclare à ce que la source qui fait foi montre à la même date.

    - encaissé déclaré ≠ somme des paiements réussis jusqu'à cette date : CONFLIT ;
    - envois déclarés < envois retrouvés jusqu'à cette date : CONFLIT ; plus d'envois ensuite : registre en retard.
    `modules` : opportunité -> module responsable.

    Le conflit est rangé sous « declaration:<module> » : c'est la déclaration qui est fausse, pas la source qui
    fait foi ; il apparaît dans la liste des conflits sans rendre incertain l'argent prouvé par le prestataire.
    """
    faits: list[Fait] = []
    alertes: list[str] = []
    for d in declarations:
        if d.indicateur == "encaisse_net":
            if encaissements is None:
                alertes.append(f"{d.module} déclare un encaissé que le prestataire de paiement n'a pas pu confirmer")
                continue
            attendus = [n for quand, n, _ in encaissements if d.date and quand[:len(d.date)] <= d.date]
            attendu = sum(attendus) if d.date else sum(n for _, n, _ in encaissements)
            if d.valeur != attendu:
                note = f"{d.module} déclare un encaissé différent du prestataire de paiement à la même date"
                faits.append(Fait("controle", "encaisse_net", d.valeur, CONFLIT, d.source,
                                  f"declaration:{d.module}", d.date, note=note, prive=True))
        elif d.indicateur == "prospects_contactes" and evenements is not None:
            siens = [e for e in evenements if modules.get(e.opportunite) == d.module and e.etape == "envoi"]
            avant = {(e.opportunite, e.ref) for e in siens if _avant(e.date, d.date) is True}
            apres = {(e.opportunite, e.ref) for e in siens if _avant(e.date, d.date) is False}
            if d.valeur < len(avant):
                faits.append(Fait("controle", "prospects_contactes", d.valeur, CONFLIT, d.source,
                                  f"declaration:{d.module}", d.date,
                                  note=f"{d.module} déclare {d.valeur} envoi(s), "
                                       f"{len(avant)} retrouvé(s) à cette date"))
            elif apres:
                alertes.append(f"registre de {d.module} en retard : {d.valeur} envoi(s) déclaré(s) au {d.date[:10]}, "
                               f"{len(apres)} prospect(s) contacté(s) depuis, non enregistré(s)")
    return faits, alertes


@dataclass
class EtatArret:
    libelle: str
    indicateur: str
    seuil: float
    sens: str
    date: str
    mesure: int | float | str | bool | None
    statut: str
    detail: str
    si_echec: str


def _atteint(valeur: float, seuil: float, sens: str) -> bool:
    return valeur >= seuil if sens == "min" else valeur <= seuil


def evaluer_arrets(o: Opportunite, c: Consolide, jour: date, previsions: list[Prevision] | None
                   ) -> list[EtatArret]:
    """Critères d'arrêt : avant la date, atteint = PROUVÉ, sinon en attente (INCONNU) ;
    après la date, atteint = PROUVÉ, manqué = ÉCHEC, non mesuré = INCONNU (verdict impossible : alerte)."""
    etats = []
    for a in o.arrets:
        v = lire(c, o.id, a.indicateur)
        echu = date.fromisoformat(a.date) <= jour
        mesurable = v.statut in (PROUVE, ECHEC) and isinstance(v.valeur, (int, float))
        if v.statut == CONFLIT:
            statut, detail = CONFLIT, "sources contradictoires : verdict impossible avant résolution"
        elif mesurable and _atteint(float(v.valeur), a.seuil, a.sens):  # type: ignore[arg-type]
            statut, detail = PROUVE, "atteint"
        elif mesurable and echu:
            statut, detail = ECHEC, "manqué à la date"
        elif echu:
            statut, detail = INCONNU, "verdict dû sans mesure"
        else:
            reste = (date.fromisoformat(a.date) - jour).days
            statut, detail = INCONNU, f"en attente, J-{reste}"
        etats.append(EtatArret(a.libelle, a.indicateur, a.seuil, a.sens, a.date, v.valeur, statut, detail,
                               a.si_echec))
    for p in previsions or []:
        if p.id not in o.previsions:
            continue
        echu = bool(p.date_verdict) and date.fromisoformat(p.date_verdict) <= jour
        if p.reel is not None:
            statut = ECHEC if p.bas is not None and p.reel < p.bas else PROUVE
            detail = f"réel {p.reel:g} (fourchette basse {p.bas:g})" if p.bas is not None else f"réel {p.reel:g}"
        elif echu:
            statut, detail = ECHEC, "verdict non rendu à la date : la boucle d'apprentissage a sauté"
        else:
            statut, detail = INCONNU, "en attente"
        etats.append(EtatArret(f"{p.id} : {p.libelle}", "prévision", p.bas or 0.0, "min", p.date_verdict,
                               p.reel, statut, detail, ""))
    return etats


def _etape_seuil(v: Valeur, seuil: float, detail: str) -> tuple[str, str]:
    if v.statut == CONFLIT:
        return CONFLIT, "sources contradictoires"
    if v.statut in (PROUVE, ECHEC) and isinstance(v.valeur, (int, float)) and v.valeur >= seuil:
        return PROUVE, detail
    return INCONNU, detail


def etats_chaine(o: Opportunite, c: Consolide, arrets: list[EtatArret]) -> dict[str, tuple[str, str]]:
    """État de chaque étape : PROUVÉ = franchie avec preuve ; ÉCHEC = un critère d'arrêt de l'étape a été
    manqué ; CONFLIT = sources contradictoires ; INCONNU = pas (encore) prouvé."""
    def n(ind: str) -> str:
        v = lire(c, o.id, ind)
        return "?" if v.valeur is None else str(v.valeur)

    etats: dict[str, tuple[str, str]] = {}
    demande = o.notes.get("demande")
    etats["opportunite"] = ((PROUVE, f"demande mesurée : {demande.source}") if demande and demande.nature == "mesuré"
                            else (INCONNU, "demande non mesurée"))
    suite = lire(c, o.id, "suite_verte")
    etats["produit"] = (suite.statut, "suite de tests rejouée" if suite.statut == PROUVE else
                        ("suite en échec" if suite.statut == ECHEC else "aucun rejeu sur le commit actuel"))
    etats["offre"] = _etape_seuil(lire(c, o.id, "offres_actives"), 1, f"{n('offres_actives')} prix actif(s)")
    etats["acheteur"] = _etape_seuil(lire(c, o.id, "prospects_qualifies"), 1,
                                     f"contactés {n('prospects_contactes')}, réponses {n('reponses')}, "
                                     f"qualifiés {n('prospects_qualifies')}")
    etats["vente"] = _etape_seuil(lire(c, o.id, "ventes_payees"), 1, f"{n('ventes_payees')} vente(s) payée(s)")
    etats["encaisse"] = _etape_seuil(lire(c, o.id, "encaisse_net"), 1, "montant en privé")
    verdicts = lire(c, o.id, "verdicts_rendus")
    if verdicts.statut == ECHEC:
        etats["amelioration"] = (ECHEC, "verdict échu non rendu")
    elif not o.previsions:
        etats["amelioration"] = (INCONNU, "aucune prévision chiffrée rattachée : rien à apprendre")
    else:
        etats["amelioration"] = _etape_seuil(verdicts, 1, f"{n('verdicts_rendus')} verdict(s) rendu(s)")
    ventes = lire(c, o.id, "ventes_payees")
    etats["croissance"] = _etape_seuil(ventes, 2, "au moins 2 ventes payées")
    for a in arrets:
        if a.statut == ECHEC and a.indicateur != "prévision":
            etape = INDICATEURS.get(a.indicateur, ("",))[0]
            if etape in etats and etats[etape][0] != PROUVE:
                etats[etape] = (ECHEC, f"critère manqué : {a.libelle}")
    return etats


def distance(etats: dict[str, tuple[str, str]]) -> int:
    """Nombre d'étapes non prouvées avant l'argent encaissé (0 = de l'argent est rentré)."""
    return sum(1 for e in JUSQU_A_L_ARGENT if etats[e][0] != PROUVE)


def conflits_de_statut(o: Opportunite, declare: str, activite: int) -> str | None:
    """Un registre qui déclare gelé, arrêté ou en préparation alors que des envois partent est faux :
    des prospects peuvent répondre sans que personne ne soit chargé de leur répondre."""
    if declare in ("gele", "arrete", "en_preparation") and activite:
        return (f"{o.id} : déclaré « {declare} » par {o.declare.get('fichier', '?')}, mais {activite} envoi(s) "
                f"ces 14 derniers jours")
    return None


def priorites(lignes: list[tuple[Opportunite, dict[str, tuple[str, str]]]]) -> list[Opportunite]:
    """Ordre de travail vers le premier euro : les opportunités actives avant les tests, puis la distance à
    l'argent, puis l'échéance la plus proche, puis le score prouvé (les hypothèses ne départagent pas)."""
    actives = [(o, e) for o, e in lignes if o.statut_mere in ("actif", "test")]

    def prochaine_echeance(o: Opportunite) -> str:
        return min((a.date for a in o.arrets), default="9999-12-31")

    # Un test (statut « test ») attend son verdict sans nouvel effort : il passe après les opportunités actives.
    actives.sort(key=lambda oe: (oe[0].statut_mere != "actif", distance(oe[1]), prochaine_echeance(oe[0]),
                                 -oe[0].score_prouve, -oe[0].confiance, oe[0].id))
    return [o for o, _ in actives]
