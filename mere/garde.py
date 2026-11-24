"""Garde anti-fuite : rien de nominatif, de financier réel ni de secret dans une sortie publique.

La garde ne corrige pas : elle refuse, et dit pourquoi. Elle s'applique au tableau public, aux rejeux et contrôles
versionnés, et à tout fichier que la CI vérifie. Dans le doute, elle refuse : un faux positif coûte une
correction, une fuite ne se rattrape pas. Elle ne voit pas un nom propre isolé : c'est pourquoi aucun adaptateur
ne recopie le contenu d'une cellule dans un message.
"""

from __future__ import annotations

import re

PREFIXES_STRIPE = ("ch", "py", "pi", "pm", "cs", "cus", "in", "ii", "il", "sub", "si", "acct", "prod", "price", "txn",
                   "re", "dp", "du", "po", "tr", "src", "card", "ba", "seti", "evt", "plink", "file", "link", "promo")
SEP = r"[\s ./-]?"
MOTIFS = {
    "adresse e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "numéro de téléphone": re.compile(
        r"(?<!\d)(?:\(?(?:\+|00)33\)?" + SEP + r"(?:\(0\))?" + SEP + r"[1-9]|0[1-9])(?:" + SEP + r"\d{2}){4}(?!\d)"),
    "SIRET ou SIREN": re.compile(
        r"(?<!\d)\d{3}[\s .-]?\d{3}[\s .-]?\d{3}(?:[\s .-]?\d{5})?(?!\d)"),
    "numéro de TVA": re.compile(r"\bFR\s?[0-9A-Z]{2}\s?\d{9}\b"),
    "identifiant Stripe": re.compile(r"\b(?:" + "|".join(PREFIXES_STRIPE) + r")_(?:live_|test_)?[A-Za-z0-9]{8,}"),
    "clé secrète": re.compile(
        r"\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{6,}|\bwhsec_[A-Za-z0-9]{6,}|_secret_[A-Za-z0-9]{6,}"
        r"|\bsk-(?:ant-)?[A-Za-z0-9_-]{10,}|\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}"
        r"|\bxox[abposr]-[A-Za-z0-9-]{10,}|\bAKIA[0-9A-Z]{16}\b|\b(?:live|test)_[A-Za-z0-9]{16,}"),
    "identifiant de message": re.compile(r"\b[0-9a-f]{16}\b"),
}
# Un montant écrit dans une sortie publique n'est accepté que s'il est l'un des prix publics déclarés.
MONTANT = re.compile(
    r"(?:(\d[\d\s .,]*)[*_]{0,2}\s?(?:k|m|md|mds|millions?|milliards?)?\s?(?:€|eur\b|euros?\b))"
    r"|(?:(?:€|\beur\b|\beuros?\b)[*_]{0,2}\s?(\d[\d\s .,]*))", re.IGNORECASE)


def fuites(texte: str, montants_publics: set[str] | None = None) -> list[str]:
    """Liste des fuites trouvées (vide = sortie publiable)."""
    trouvees = []
    for nom, motif in MOTIFS.items():
        for m in motif.finditer(texte):
            trouvees.append(f"{nom} : « {m.group(0)[:40]} »")
    autorises = {re.sub(r"\s", "", x) for x in (montants_publics or set())}
    for m in MONTANT.finditer(texte):
        brut = re.sub(r"[\s ]", "", m.group(1) or m.group(2) or "").rstrip(".,")
        if brut not in autorises:
            trouvees.append(f"montant non déclaré public : « {m.group(0).strip()[:30]} »")
    return trouvees
