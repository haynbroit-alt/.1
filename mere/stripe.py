"""Lecture seule du prestataire de paiement : la seule source qui fait foi pour l'argent encaissé.

Garanties :
- seules des requêtes GET partent, et seulement vers une liste fermée de chemins de lecture ;
- un paiement compte s'il est réussi, en mode réel, dans la devise de l'entreprise, net de ses remboursements ;
- une facture émise non payée est du CA annoncé, jamais de l'encaissé ; un potentiel n'est jamais lu ici ;
- un refus de lecture donne INCONNU, jamais zéro.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .faits import TOUTE_L_ENTREPRISE, Fait
from .statuts import ECHEC, INCONNU, PROUVE

API = "https://api.stripe.com/v1"
CHEMINS_AUTORISES = ("charges", "invoices", "products", "prices", "subscriptions", "balance_transactions",
                     "payouts", "disputes")
MODULE = "stripe"
NON_ATTRIBUE = "non-attribue"


class LectureImpossible(Exception):
    """La source n'a pas pu être lue : le résultat est INCONNU, pas nul."""


@dataclass
class ClientLecture:
    """Client HTTP minimal, en lecture seule. `ouvrir` est injectable pour les tests."""

    ouvrir: Callable[[urllib.request.Request], Any] | None = None
    cle: str | None = None

    def get(self, chemin: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if chemin not in CHEMINS_AUTORISES:
            raise PermissionError(f"chemin hors lecture autorisée : {chemin!r}")
        requete = urllib.request.Request(
            f"{API}/{chemin}?{urllib.parse.urlencode(params or {}, doseq=True)}", method="GET"
        )
        # Dans l'environnement cloud, le mandataire réseau injecte la clé ; ailleurs, une clé restreinte
        # en lecture est attendue dans STRIPE_CLE_LECTURE.
        cle = self.cle or os.environ.get("STRIPE_CLE_LECTURE") or "rk_lecture_via_mandataire"
        requete.add_header("Authorization", f"Bearer {cle}")
        ouvrir = self.ouvrir or (lambda r: urllib.request.urlopen(r, timeout=30))  # noqa: S310
        try:
            with ouvrir(requete) as reponse:
                donnees = json.loads(reponse.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise LectureImpossible(f"{chemin} : HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise LectureImpossible(f"{chemin} : {exc}") from exc
        if not isinstance(donnees, dict) or "error" in donnees:
            raise LectureImpossible(f"{chemin} : réponse d'erreur")
        return donnees


def lister(client: ClientLecture, chemin: str, params: dict[str, Any] | None = None,
           pages_max: int = 50) -> list[dict[str, Any]]:
    """Toutes les pages d'une liste. Au-delà de `pages_max` pages, la lecture est déclarée incomplète."""
    elements: list[dict[str, Any]] = []
    p = {"limit": 100, **(params or {})}
    for _ in range(pages_max):
        page = client.get(chemin, p)
        donnees = page.get("data") or []
        elements.extend(donnees)
        if not page.get("has_more") or not donnees:
            return elements
        p["starting_after"] = donnees[-1]["id"]
    raise LectureImpossible(f"{chemin} : plus de {pages_max} pages, lecture incomplète")


@dataclass
class Releve:
    faits: list[Fait] = field(default_factory=list)
    encaissements: list[tuple[str, int, str]] = field(default_factory=list)  # (date ISO, net, opportunité)
    erreurs: list[str] = field(default_factory=list)
    virements: list[dict[str, Any]] | None = None  # None : non lus
    grand_livre: dict[str, Any] = field(default_factory=dict)  # concordance paiements / grand livre


def _date(ts: int | None) -> str:
    return datetime.fromtimestamp(ts or 0, UTC).isoformat(timespec="seconds")


def _attribuer(charge: dict[str, Any], noms_produits: dict[str, str], factures: dict[str, list[str]],
               correspondances: dict[str, list[str]]) -> str:
    """Opportunité d'un paiement : métadonnée explicite, puis produit de la facture, puis description."""
    meta = (charge.get("metadata") or {}).get("opportunite")
    if meta in correspondances:
        return str(meta)
    textes = [noms_produits.get(pid, "") for pid in factures.get(charge.get("invoice") or "", [])]
    textes.append(charge.get("description") or "")
    candidates = {opp for opp, motifs in correspondances.items()
                  if any(m.lower() in t.lower() for m in motifs for t in textes if t)}
    # Plusieurs opportunités possibles (« Pack » et « Pack Pro ») : on n'attribue pas au hasard.
    return candidates.pop() if len(candidates) == 1 else NON_ATTRIBUE


def releve(client: ClientLecture, correspondances: dict[str, list[str]], devise: str = "eur",
           maintenant: datetime | None = None, opportunites: list[str] | None = None) -> Releve:
    """Relève l'argent réellement encaissé, par opportunité. `correspondances` : opportunité -> noms de produits.

    Une opportunité sans paiement attribué vaut 0 PROUVÉ seulement si aucun paiement réussi n'est resté sans
    attribution ; sinon elle est INCONNU (l'argent non attribué pourrait être le sien)."""
    quand = (maintenant or datetime.now(UTC)).isoformat(timespec="seconds")
    devise = devise.lower()
    r = Releve()
    source = "api.stripe.com (lecture seule)"
    try:
        charges = lister(client, "charges")
    except LectureImpossible as exc:
        r.erreurs.append(str(exc))
        for ind in ("encaisse_net", "ventes_payees"):
            r.faits.append(Fait(MODULE, ind, None, INCONNU, source, date=quand,
                                note=f"lecture impossible : {exc}", prive=ind == "encaisse_net"))
        return r

    try:
        produits = lister(client, "products")
    except LectureImpossible as exc:
        produits = []
        r.erreurs.append(str(exc))
    noms = {p["id"]: p.get("name") or "" for p in produits}

    factures: dict[str, list[str]] = {}
    ouvertes: list[dict[str, Any]] = []
    try:
        for f in lister(client, "invoices"):
            lignes = ((f.get("lines") or {}).get("data")) or []
            factures[f["id"]] = [
                ((ligne.get("price") or {}).get("product") or "") for ligne in lignes
            ]
            if f.get("status") == "open" and f.get("livemode"):
                ouvertes.append(f)
        factures_lues = True
    except LectureImpossible as exc:
        r.erreurs.append(str(exc))
        factures_lues = False

    # Litiges : un paiement contesté n'est pas acquis ; perdu, il est repris.
    litiges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    try:
        for d in lister(client, "disputes"):
            litiges[str(d.get("charge") or "")].append(d)
        litiges_lus = True
    except LectureImpossible as exc:
        r.erreurs.append(str(exc))
        litiges_lus = False

    net: dict[str, int] = defaultdict(int)
    rembourse: dict[str, int] = defaultdict(int)
    ventes: dict[str, int] = defaultdict(int)
    echecs: dict[str, list[str]] = defaultdict(list)
    ids: dict[str, list[str]] = defaultdict(list)
    incertain: dict[str, list[str]] = defaultdict(list)
    reussis: list[dict[str, Any]] = []
    ignores = {"mode_test": 0, "autre_devise": 0}

    for c in charges:
        if not c.get("livemode"):
            ignores["mode_test"] += 1
            continue
        if (c.get("currency") or "").lower() != devise:
            ignores["autre_devise"] += 1
            continue
        opp = _attribuer(c, noms, factures, correspondances)
        if c.get("status") == "succeeded" and c.get("paid") and c.get("captured") is False:
            # Autorisation jamais capturée : aucun argent n'a bougé.
            for cle in (opp, TOUTE_L_ENTREPRISE):
                echecs[cle].append("autorisation non capturée")
            continue
        if c.get("status") == "succeeded" and c.get("paid"):
            reussis.append(c)
            montant = int(c.get("amount") or 0)
            rembourse_c = min(int(c.get("amount_refunded") or 0), montant)
            perdus = sum(int(d.get("amount") or 0) for d in litiges.get(c["id"], []) if d.get("status") == "lost")
            repris = min(perdus, montant - rembourse_c)
            ouverts = [d for d in litiges.get(c["id"], []) if d.get("status") not in ("won", "lost")]
            if c.get("disputed") and not litiges.get(c["id"]):
                ouverts = [{"status": "inconnu"}]  # contesté, sans fiche de litige lisible : argent non acquis
            for cle in (opp, TOUTE_L_ENTREPRISE):
                net[cle] += montant - rembourse_c - repris
                rembourse[cle] += rembourse_c
                ids[cle].append(c["id"])
                if rembourse_c + repris < montant:
                    ventes[cle] += 1
                if ouverts:
                    incertain[cle].append("litige en cours")
                if not litiges_lus:
                    incertain[cle].append("litiges illisibles")
            r.encaissements.append((_date(c.get("created")), montant - rembourse_c - repris, opp))
        else:
            issue = c.get("outcome") or {}
            motif = "carte de test en mode réel" if issue.get("reason") == "live_mode_test_card" else (
                issue.get("reason") or c.get("failure_code") or c.get("status") or "refus")
            for cle in (opp, TOUTE_L_ENTREPRISE):
                echecs[cle].append(motif)

    preuve = f"/v1/charges : {len(charges)} paiement(s) lus le {quand[:10]}"
    note_ign = ", ".join(f"{k} : {v}" for k, v in ignores.items() if v)
    cles = set(net) | set(echecs) | {TOUTE_L_ENTREPRISE}
    # Un paiement réussi sans attribution pourrait appartenir à n'importe quelle opportunité : aucune ne peut
    # alors afficher un total PROUVÉ, même celle qui a déjà des paiements (ce total ne serait qu'un minimum).
    orphelin = bool(ids.get(NON_ATTRIBUE))
    for opp in opportunites or []:
        cles.add(opp)
    for cle in sorted(cles):
        if orphelin and cle not in (TOUTE_L_ENTREPRISE, NON_ATTRIBUE):
            for ind in ("encaisse_net", "ventes_payees"):
                r.faits.append(Fait(MODULE, ind, None, INCONNU, source, cle, quand, prive=ind == "encaisse_net",
                                    note="des paiements réussis ne sont attribués à aucune opportunité"))
            motifs = echecs.get(cle, [])
            r.faits.append(Fait(MODULE, "paiements_echoues", len(motifs), ECHEC if motifs else PROUVE, source,
                                cle, quand, preuve, note="; ".join(sorted(set(motifs)))))
            continue
        extra = {"ids": ids.get(cle, [])}
        doutes = sorted(set(incertain.get(cle, [])))
        notes = [("ignorés : " + note_ign) if note_ign else "", *doutes]
        if doutes:
            r.faits.append(Fait(MODULE, "encaisse_net", None, INCONNU, source, cle, quand, prive=True,
                                note="; ".join(n for n in notes if n), extra=extra))
        else:
            r.faits.append(Fait(MODULE, "encaisse_net", net.get(cle, 0), PROUVE, source, cle, quand, preuve,
                                note="; ".join(n for n in notes if n), prive=True, extra=extra))
        r.faits.append(Fait(MODULE, "remboursements", rembourse.get(cle, 0), PROUVE, source, cle, quand,
                            preuve, prive=True))
        if doutes:  # un paiement contesté n'est pas encore une vente acquise
            r.faits.append(Fait(MODULE, "ventes_payees", None, INCONNU, source, cle, quand, note="; ".join(doutes)))
        else:
            r.faits.append(Fait(MODULE, "ventes_payees", ventes.get(cle, 0), PROUVE, source, cle, quand, preuve))
        motifs = echecs.get(cle, [])
        r.faits.append(Fait(MODULE, "paiements_echoues", len(motifs), ECHEC if motifs else PROUVE, source,
                            cle, quand, preuve, note="; ".join(sorted(set(motifs)))))

    if factures_lues:
        total = sum(int(f.get("amount_due") or 0) for f in ouvertes)
        r.faits.append(Fait(MODULE, "ca_annonce", total, PROUVE, source, TOUTE_L_ENTREPRISE, quand,
                            f"/v1/invoices : {len(ouvertes)} facture(s) ouverte(s)", prive=True,
                            note="annoncé, non encaissé"))

    # Une offre n'est en vente que si son produit est réel (mode réel), actif, et porte un prix actif.
    try:
        prix = lister(client, "prices", {"active": "true"})
        avec_prix = {str(x.get("product")) for x in prix if x.get("active") and x.get("livemode")}
        prix_lus = True
    except LectureImpossible as exc:
        r.erreurs.append(str(exc))
        avec_prix, prix_lus = set(), False
    actifs = [p for p in produits if p.get("active") and p.get("livemode") and p.get("id") in avec_prix]
    if not prix_lus:
        produits = []
    for opp, motifs in correspondances.items():
        n = sum(1 for p in actifs if any(m.lower() in (p.get("name") or "").lower() for m in motifs))
        r.faits.append(Fait(MODULE, "offres_actives", n, PROUVE if produits else INCONNU, source, opp, quand,
                            f"/v1/products : {len(actifs)} produit(s) actif(s)" if produits else ""))
    if produits:
        r.faits.append(Fait(MODULE, "offres_actives", len(actifs), PROUVE, source, TOUTE_L_ENTREPRISE, quand,
                            f"/v1/products : {len(actifs)} produit(s) actif(s)"))

    try:
        abos = lister(client, "subscriptions", {"status": "active"})
        r.faits.append(Fait(MODULE, "abonnements_actifs", len(abos), PROUVE, source, TOUTE_L_ENTREPRISE, quand,
                            f"/v1/subscriptions : {len(abos)} actif(s)"))
    except LectureImpossible as exc:
        r.faits.append(Fait(MODULE, "abonnements_actifs", None, INCONNU, source, date=quand,
                            note=f"lecture refusée : {exc}"))

    # Grand livre : chaque paiement réussi doit y avoir son mouvement, du même montant (contrôle croisé).
    try:
        mouvements = lister(client, "balance_transactions")
        par_source = {str(m.get("source") or ""): m for m in mouvements if m.get("type") in ("charge", "payment")}
        frais = sum(int(m.get("fee") or 0) for m in par_source.values())
        ecarts = []
        for c in reussis:
            m = par_source.get(c["id"])
            if m is None:
                ecarts.append("paiement réussi absent du grand livre")
            elif int(m.get("amount") or 0) != int(c.get("amount") or 0):
                ecarts.append("montant différent entre paiement et grand livre")
        r.grand_livre = {"lu": True, "verifies": len(reussis) - len(ecarts), "ecarts": ecarts}
        r.faits.append(Fait(MODULE, "frais_paiement", frais, PROUVE, source, TOUTE_L_ENTREPRISE, quand,
                            f"/v1/balance_transactions : {len(mouvements)} mouvement(s)", prive=True))
    except LectureImpossible as exc:
        r.grand_livre = {"lu": False, "verifies": 0, "ecarts": [], "erreur": str(exc)}
        r.faits.append(Fait(MODULE, "frais_paiement", None, INCONNU, source, date=quand, prive=True,
                            note=f"lecture refusée : {exc}"))

    # Virements vers la banque : ce que le prestataire dit avoir versé (la banque le confirme ailleurs).
    try:
        r.virements = lister(client, "payouts")
        verse = sum(int(v.get("amount") or 0) for v in r.virements if v.get("status") == "paid" and v.get("livemode"))
        r.faits.append(Fait(MODULE, "verse_en_banque", verse, PROUVE, source, TOUTE_L_ENTREPRISE, quand,
                            f"/v1/payouts : {len(r.virements)} virement(s)", prive=True))
    except LectureImpossible as exc:
        r.faits.append(Fait(MODULE, "verse_en_banque", None, INCONNU, source, date=quand, prive=True,
                            note=f"lecture refusée : {exc}"))
    ouverts_total = sum(1 for liste in litiges.values() for d in liste if d.get("status") not in ("won", "lost"))
    r.faits.append(Fait(MODULE, "litiges_ouverts", ouverts_total if litiges_lus else None,
                        PROUVE if litiges_lus else INCONNU, source, TOUTE_L_ENTREPRISE, quand,
                        "/v1/disputes" if litiges_lus else ""))
    return r
