"""La chaîne opportunité → produit → offre → acheteur → vente → encaissé → amélioration → croissance.

Consolidation des faits, rapprochement des déclarations avec l'argent réellement encaissé, état de chaque
étape, critères d'arrêt et priorité. Rien ici ne lit le réseau : tout part des faits déjà relevés.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from .faits import INDICATEURS, TOUTE_L_ENTREPRISE, Fait
from .portefeuille import Opportunite
from .sources import Declaration, Evenement, Prevision, instant, jour_de
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
    """L'événement précède-t-il la déclaration ? Comparaison en instants UTC (fuseaux convertis).
    None si on ne peut pas le dire : date illisible, ou même jour quand l'une des deux n'a pas d'heure."""
    ie, idc = instant(evenement), instant(declaration)
    if ie is not None and idc is not None:
        return ie <= idc
    je, jd = jour_de(evenement), jour_de(declaration)
    if je is None or jd is None or je == jd:
        return None
    return je < jd


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
            # Le périmètre de la déclaration : toute l'entreprise, ou seulement les opportunités du module.
            siens = [(q, n, o) for q, n, o in encaissements if d.perimetre == "*" or modules.get(o) == d.perimetre]
            orphelins = d.perimetre != "*" and any(o not in modules for _, _, o in encaissements)
            positions = [_avant(q, d.date) if d.date else True for q, _, _ in siens]
            surs = sum(n for (_, n, _), av in zip(siens, positions, strict=True) if av is True)
            douteux = sum(n for (_, n, _), av in zip(siens, positions, strict=True) if av is None)
            if surs <= d.valeur <= surs + douteux and (douteux == 0 or d.valeur in (surs, surs + douteux)):
                continue
            if douteux or orphelins:
                alertes.append(f"{d.module} déclare un encaissé que l'on ne peut ni confirmer ni contredire à sa date "
                               "(paiement du même jour sans heure, ou paiement non attribué)")
                continue
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


# Indicateurs qui ne peuvent que croître : sous le seuil aujourd'hui, ils l'étaient à toute date passée.
# (Pas les comptes issus de contrôles qui peuvent expirer, comme prospects_reels ou qualifies_verifies.)
CROISSANTS = {"prospects_contactes", "envois_bloques", "reponses", "prospects_qualifies", "conversions",
              "ventes_payees", "paiements_echoues", "verdicts_dus"}
MesureADate = Callable[[str, str, date], "tuple[int | float, str] | None"]


def evaluer_arrets(o: Opportunite, c: Consolide, jour: date, previsions: list[Prevision] | None,
                   mesure_a_date: MesureADate | None = None) -> list[EtatArret]:
    """Critères d'arrêt.
    - Avant la date : un seuil minimal déjà atteint est PROUVÉ (les comptes ne font que croître) ; un plafond
      (« au plus ») ne peut pas être confirmé avant la fin : en attente.
    - Après la date : on juge la valeur **à la date du critère**, jamais un résultat arrivé après. Atteint =
      PROUVÉ, manqué = ÉCHEC ; sans mesure datée = INCONNU (verdict impossible : alerte)."""
    etats = []
    for a in o.arrets:
        v = lire(c, o.id, a.indicateur)
        limite = date.fromisoformat(a.date)
        echu = limite <= jour
        if v.statut == CONFLIT:
            statut, detail, mesure = CONFLIT, "sources contradictoires : verdict impossible avant résolution", v.valeur
        elif echu:
            datee = mesure_a_date(o.id, a.indicateur, limite) if mesure_a_date else None
            croissant = a.indicateur in CROISSANTS and v.statut == PROUVE and isinstance(v.valeur, (int, float))
            if datee is None and croissant and a.sens == "min" and not _atteint(float(v.valeur), a.seuil, a.sens):
                # Un compte qui ne fait que croître est sous le seuil aujourd'hui : il l'était à la date.
                statut, detail, mesure = ECHEC, "manqué : la valeur actuelle est déjà sous le seuil", v.valeur
            elif datee is None:
                statut, detail, mesure = INCONNU, "verdict dû sans mesure", None
            elif datee[1] not in (PROUVE, ECHEC):
                statut, detail, mesure = INCONNU, "verdict dû sans mesure", datee[0]
            else:
                mesure = datee[0]
                ok = _atteint(float(mesure), a.seuil, a.sens)
                statut, detail = (PROUVE, "atteint à la date") if ok else (ECHEC, "manqué à la date")
        else:
            mesure = v.valeur
            mesurable = v.statut in (PROUVE, ECHEC) and isinstance(v.valeur, (int, float))
            if a.sens == "min" and mesurable and _atteint(float(v.valeur), a.seuil, a.sens):  # type: ignore[arg-type]
                statut, detail = PROUVE, "atteint"
            else:
                statut, detail = INCONNU, f"en attente, J-{(limite - jour).days}"
        etats.append(EtatArret(a.libelle, a.indicateur, a.seuil, a.sens, a.date, mesure, statut, detail,
                               a.si_echec))
    for p in previsions or []:
        if p.id not in o.previsions:
            continue
        echu = bool(p.date_verdict) and date.fromisoformat(p.date_verdict) <= jour
        if p.reel is not None:
            if p.sens == "moins":
                plafond = next((x for x in (p.haut, p.central, p.bas) if x is not None), None)
                statut = ECHEC if plafond is not None and p.reel > plafond else PROUVE
                detail = f"réel {p.reel:g} (plafond {plafond:g}, moins = mieux)" if plafond is not None else \
                    f"réel {p.reel:g}"
            else:
                statut = ECHEC if p.bas is not None and p.reel < p.bas else PROUVE
                detail = f"réel {p.reel:g} (fourchette basse {p.bas:g})" if p.bas is not None else f"réel {p.reel:g}"
        elif echu:
            statut, detail = ECHEC, "verdict non rendu à la date : la boucle d'apprentissage a sauté"
        else:
            statut, detail = INCONNU, "en attente"
        etats.append(EtatArret(f"{p.id} : {p.libelle}", "prévision", p.bas or 0.0, "min", p.date_verdict,
                               p.reel, statut, detail, ""))
    return etats


def _note_de(v: Valeur) -> str:
    return "; ".join(sorted({f.note for f in v.faits if f.note}))


def _etape_seuil(v: Valeur, seuil: float, detail: str) -> tuple[str, str]:
    if v.statut == CONFLIT:
        return CONFLIT, "sources contradictoires"
    if v.statut in (PROUVE, ECHEC) and isinstance(v.valeur, (int, float)) and v.valeur >= seuil:
        return PROUVE, detail
    return INCONNU, detail


def etats_chaine(o: Opportunite, c: Consolide, arrets: list[EtatArret],
                 controles: dict[str, tuple[str, str]] | None = None) -> dict[str, tuple[str, str]]:
    """État de chaque étape : PROUVÉ = franchie avec preuve vérifiée par un autre acteur que son producteur ;
    ÉCHEC = un critère d'arrêt de l'étape a été manqué ; CONFLIT = sources contradictoires ; INCONNU = pas
    (encore) prouvé. `controles` : identifiant de contrôle -> (statut, détail)."""
    ctrl = controles or {}

    def n(ind: str) -> str:
        v = lire(c, o.id, ind)
        return "?" if v.valeur is None else str(v.valeur)

    def verifie(etat: tuple[str, str], cle: str, quoi: str) -> tuple[str, str]:
        """Une étape franchie n'est PROUVÉE que si le contrôle indépendant `cle` l'est aussi."""
        if etat[0] != PROUVE:
            return etat
        statut, detail = ctrl.get(cle, (INCONNU, "aucun contrôle indépendant"))
        if statut == PROUVE:
            return etat
        return (CONFLIT if statut == CONFLIT else INCONNU), f"{etat[1]}, mais {quoi} : {detail}"

    etats: dict[str, tuple[str, str]] = {}
    demande = o.notes.get("demande")
    if demande and demande.nature == "mesuré":
        etats["opportunite"] = verifie((PROUVE, f"demande mesurée : {demande.source}"), f"citation:{o.id}/demande",
                                       "source non confirmée")
    else:
        etats["opportunite"] = (INCONNU, "demande non mesurée")
    suite = lire(c, o.id, "suite_verte")
    etats["produit"] = (suite.statut, "suite rejouée deux fois en clone propre" if suite.statut == PROUVE else
                        ("suite en échec" if suite.statut == ECHEC else
                         _note_de(suite) or "aucun rejeu sur le commit actuel"))
    etats["offre"] = _etape_seuil(lire(c, o.id, "offres_actives"), 1, f"{n('offres_actives')} prix actif(s)")
    etats["acheteur"] = _etape_seuil(lire(c, o.id, "qualifies_verifies"), 1,
                                     f"contactés {n('prospects_contactes')} (dont réels vérifiés "
                                     f"{n('prospects_reels')}), réponses {n('reponses')}, qualifiés "
                                     f"{n('prospects_qualifies')} (vérifiés {n('qualifies_verifies')})")
    etats["vente"] = verifie(_etape_seuil(lire(c, o.id, "ventes_payees"), 1, f"{n('ventes_payees')} vente(s) payée(s)"),
                             "argent:grand-livre", "paiement non rapproché du grand livre")
    # Encaissé : l'argent de l'opportunité est reçu ET tout l'argent reçu par l'entreprise est retrouvé au crédit
    # du relevé bancaire (la banque est le contrôleur, pas le prestataire de paiement).
    enc = lire(c, o.id, "encaisse_net")
    total, credite = lire(c, TOUTE_L_ENTREPRISE, "encaisse_net"), lire(c, TOUTE_L_ENTREPRISE, "credite_en_banque")
    frais = lire(c, TOUTE_L_ENTREPRISE, "frais_paiement")
    banque = ctrl.get("argent:credite-en-banque", (INCONNU, "aucun rapprochement bancaire"))
    if enc.statut == CONFLIT:
        etats["encaisse"] = (CONFLIT, "sources contradictoires")
    elif enc.statut == PROUVE and isinstance(enc.valeur, int) and enc.valeur > 0:
        # Le prestataire vire l'encaissé net de ses frais : c'est ce montant qui doit être retrouvé en banque.
        du = (total.valeur - frais.valeur) if isinstance(total.valeur, int) and isinstance(frais.valeur, int) \
            and frais.statut == PROUVE else None
        en_banque = (banque[0] == PROUVE and credite.statut == PROUVE and isinstance(credite.valeur, int)
                     and du is not None and credite.valeur >= du)
        etats["encaisse"] = ((PROUVE, "crédité en banque, montant en privé") if en_banque else
                             (INCONNU, f"paiement réussi, crédit en banque non vérifié : {banque[1]}"))
    else:
        etats["encaisse"] = (INCONNU, "aucun argent reçu" if enc.statut == PROUVE else (_note_de(enc) or "non relu"))
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
