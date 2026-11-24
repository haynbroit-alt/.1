"""Le contrat commun : un fait.

Chaque module de l'écosystème partage ses résultats sous cette forme, sans importer le code d'un autre module.
Un fait dit QUI l'a produit, SUR QUOI (opportunité, indicateur), COMBIEN, avec QUEL statut, OÙ le vérifier.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .statuts import PROUVE, STATUTS

TOUTE_L_ENTREPRISE = "*"

# Indicateur -> (étape de la chaîne, unité, définition). Les montants sont en centimes, jamais en float.
INDICATEURS: dict[str, tuple[str, str, str]] = {
    "visiteurs": ("acheteur", "visites", "Visiteurs uniques mesurés par un compteur sur la page de l'offre"),
    "prospects_contactes": ("acheteur", "prospects", "Prospects distincts ayant reçu au moins un message"),
    "envois_bloques": ("acheteur", "prospects", "Messages retenus par un filtre (défi anti-spam, rebond)"),
    "reponses": ("acheteur", "prospects", "Prospects distincts ayant répondu, quel que soit le sens"),
    "prospects_qualifies": ("acheteur", "prospects", "Prospects avec besoin, budget et décideur confirmés"),
    "prospects_reels": ("acheteur", "prospects", "Prospects contactés dont l'existence est vérifiée par le web public"),
    "qualifies_verifies": ("acheteur", "prospects", "Prospects qualifiés dont l'existence est vérifiée"),
    "conversions": ("vente", "prospects", "Prospects ayant accepté une proposition (avant paiement)"),
    "ventes_payees": ("vente", "ventes", "Paiements réussis en mode réel, non remboursés en totalité"),
    "paiements_echoues": ("vente", "paiements", "Tentatives de paiement refusées ou annulées"),
    "remboursements": ("encaisse", "centimes", "Montant remboursé"),
    "encaisse_net": ("encaisse", "centimes", "Paiements réussis en mode réel, moins remboursements et litiges perdus"),
    "litiges_ouverts": ("encaisse", "litiges", "Contestations de paiement en cours : l'argent n'est pas acquis"),
    "verse_en_banque": ("encaisse", "centimes", "Virements du prestataire vers la banque, déclarés versés par lui"),
    "credite_en_banque": ("encaisse", "centimes", "Virements retrouvés au crédit du relevé bancaire du propriétaire"),
    "ca_annonce": ("vente", "centimes", "Factures émises non payées : jamais compté comme encaissé"),
    "frais_paiement": ("encaisse", "centimes", "Frais du prestataire de paiement"),
    "couts": ("encaisse", "centimes", "Dépenses directes engagées"),
    "heures": ("encaisse", "heures", "Temps du fondateur passé sur l'opportunité"),
    "benefice_net": ("encaisse", "centimes", "Encaissé net moins frais et coûts (temps non compté)"),
    "offres_actives": ("offre", "produits", "Produits actifs avec un prix chez le prestataire de paiement"),
    "abonnements_actifs": ("croissance", "abonnements", "Abonnements actifs"),
    "verdicts_dus": ("amelioration", "verdicts", "Prévisions dont la date de verdict est passée"),
    "verdicts_rendus": ("amelioration", "verdicts", "Prévisions dues dont le résultat réel est écrit"),
    "suite_verte": ("produit", "booléen", "La suite de tests du module passe, ligne de bilan vue"),
    "statut_declare": ("opportunite", "texte", "Statut que le registre d'un module déclare pour l'opportunité"),
}

# Indicateurs cumulés : une valeur plus récente ne peut pas être plus petite qu'une plus ancienne.
CUMULES = {"prospects_contactes", "envois_bloques", "reponses", "ventes_payees", "paiements_echoues",
           "remboursements", "encaisse_net"}
MONETAIRES = {k for k, v in INDICATEURS.items() if v[1] == "centimes"}


@dataclass(frozen=True)
class Fait:
    module: str
    indicateur: str
    valeur: int | float | str | bool | None
    statut: str
    source: str
    opportunite: str = TOUTE_L_ENTREPRISE
    date: str = ""
    preuve: str = ""
    note: str = ""
    prive: bool = False
    extra: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        if self.statut not in STATUTS:
            raise ValueError(f"statut invalide : {self.statut!r}")
        if self.indicateur not in INDICATEURS:
            raise ValueError(f"indicateur hors contrat : {self.indicateur!r}")
        if not self.module or not self.source:
            raise ValueError("un fait sans module ni source n'est pas un fait")
        if self.statut == PROUVE and (self.valeur is None or not self.preuve):
            raise ValueError(f"PROUVÉ exige une valeur et une preuve ({self.module}/{self.indicateur})")
        if self.indicateur in MONETAIRES:
            if not isinstance(self.valeur, (int, type(None))) or isinstance(self.valeur, bool):
                raise ValueError(f"montant en centimes entiers exigé ({self.indicateur})")
            if not self.prive:
                raise ValueError(f"un montant est toujours privé ({self.indicateur})")

    @property
    def etape(self) -> str:
        return INDICATEURS[self.indicateur][0]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not d["extra"]:
            d.pop("extra")
        return d


def lire_jsonl(lignes: list[str], module_attendu: str | None = None) -> tuple[list[Fait], list[str]]:
    """Lit des faits publiés par un module. Une ligne invalide est rejetée et signalée, jamais corrigée."""
    faits: list[Fait] = []
    erreurs: list[str] = []
    for n, ligne in enumerate(lignes, 1):
        if not ligne.strip():
            continue
        try:
            brut = json.loads(ligne)
            if module_attendu and brut.get("module") != module_attendu:
                raise ValueError(f"module {brut.get('module')!r} au lieu de {module_attendu!r}")
            faits.append(Fait(**brut))
        except (ValueError, TypeError) as exc:
            erreurs.append(f"ligne {n} : {exc}")
    return faits, erreurs
