"""Garde anti-fuite : rien de nominatif, de financier réel ni de secret dans une sortie publique.

La garde ne corrige pas : elle refuse, et dit pourquoi. Elle s'applique au tableau public, aux rejeux
versionnés et à tout fichier que la CI vérifie.
"""

from __future__ import annotations

import re

MOTIFS = {
    "adresse e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "numéro de téléphone": re.compile(r"(?<!\d)(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}(?!\d)"),
    "SIRET ou SIREN": re.compile(r"(?<![\d.,])\d{3}\s?\d{3}\s?\d{3}(?:\s?\d{5})?(?![\d.,])"),
    "identifiant Stripe": re.compile(r"\b(?:ch|py|pi|cus|in|sub|acct|prod|price|txn|re)_[A-Za-z0-9]{8,}\b"),
    "clé secrète": re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{6,}|\bgh[pousr]_[A-Za-z0-9]{20,}"),
    "identifiant de message": re.compile(r"\b[0-9a-f]{16}\b"),
}
# Un montant en euros écrit dans une sortie publique n'est accepté que s'il est l'un des prix publics déclarés.
MONTANT = re.compile(r"(\d[\d\s .,]*)\s?€")


def fuites(texte: str, montants_publics: set[str] | None = None) -> list[str]:
    """Liste des fuites trouvées (vide = sortie publiable)."""
    trouvees = []
    for nom, motif in MOTIFS.items():
        for m in motif.finditer(texte):
            trouvees.append(f"{nom} : « {m.group(0)[:40]} »")
    autorises = {re.sub(r"\s", "", x) for x in (montants_publics or set())}
    for m in MONTANT.finditer(texte):
        brut = re.sub(r"[\s ]", "", m.group(1))
        if brut not in autorises:
            trouvees.append(f"montant non déclaré public : « {m.group(0).strip()} »")
    return trouvees
