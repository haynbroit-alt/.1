"""Le portefeuille d'opportunités et la grille des six critères de la mission.

Critères : demande réelle, concurrence, marge, coût d'acquisition, vitesse de vente, potentiel. Chaque note
(0 à 5) porte sa nature : « mesuré » (avec sa source), « calcul » ou « hypothèse ». Le score PROUVÉ ne compte
que les notes mesurées : une hypothèse ne fait jamais monter une opportunité dans le classement prouvé.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .faits import INDICATEURS

CRITERES = ("demande", "concurrence", "marge", "cac", "vitesse", "potentiel")
LIBELLES_CRITERES = {"demande": "Demande réelle", "concurrence": "Concurrence", "marge": "Marge",
                     "cac": "Coût d'acquisition", "vitesse": "Vitesse de vente", "potentiel": "Potentiel"}
NATURES = ("mesuré", "calcul", "hypothèse")
STATUTS_MERE = ("actif", "test", "gele", "arrete")
SENS = ("min", "max")


@dataclass(frozen=True)
class Note:
    critere: str
    note: int
    nature: str
    source: str
    justification: str
    verif: dict[str, Any] | None = None  # comment un autre acteur vérifie la source (page publique ou données)


@dataclass(frozen=True)
class Arret:
    libelle: str
    indicateur: str
    seuil: float
    sens: str
    date: str
    si_echec: str


@dataclass
class Opportunite:
    id: str
    nom: str
    module: str
    statut_mere: str
    responsable: str
    prochaine_action: str
    stripe_produits: list[str] = field(default_factory=list)
    previsions: list[str] = field(default_factory=list)
    declare: dict[str, str] = field(default_factory=dict)
    rejeu: str = ""
    notes: dict[str, Note] = field(default_factory=dict)
    arrets: list[Arret] = field(default_factory=list)
    # Critères dont la source a été vérifiée par un autre acteur (rempli par les contrôles de citation).
    notes_verifiees: set[str] = field(default_factory=set)

    @property
    def score_total(self) -> int:
        return sum(n.note for n in self.notes.values())

    @property
    def score_prouve(self) -> int:
        """Seules comptent les notes mesurées dont la source a été confirmée par un autre acteur."""
        return sum(n.note for k, n in self.notes.items() if n.nature == "mesuré" and k in self.notes_verifiees)

    @property
    def confiance(self) -> float:
        return sum(1 for k, n in self.notes.items() if n.nature == "mesuré" and k in self.notes_verifiees) / len(
            CRITERES)


def _opportunite(brut: dict[str, Any], erreurs: list[str]) -> Opportunite | None:
    oid = str(brut.get("id") or "").strip()
    if not oid:
        erreurs.append("opportunité sans identifiant")
        return None
    o = Opportunite(oid, str(brut.get("nom") or oid), str(brut.get("module") or ""),
                    str(brut.get("statut") or ""), str(brut.get("responsable") or ""),
                    str(brut.get("prochaine_action") or ""), list(brut.get("stripe_produits") or []),
                    list(brut.get("previsions") or []), dict(brut.get("declare") or {}), str(brut.get("rejeu") or ""))
    if o.statut_mere not in STATUTS_MERE:
        erreurs.append(f"{oid} : statut {o.statut_mere!r} hors de {STATUTS_MERE}")
    if not o.module:
        erreurs.append(f"{oid} : module responsable manquant")
    for critere in CRITERES:
        c = (brut.get("criteres") or {}).get(critere)
        if c is None:
            erreurs.append(f"{oid} : critère {critere!r} absent (écrire note 0, nature hypothèse si inconnu)")
            continue
        note, nature, source = c.get("note"), c.get("nature"), str(c.get("source") or "")
        if not isinstance(note, int) or isinstance(note, bool) or not 0 <= note <= 5:
            erreurs.append(f"{oid}/{critere} : note entière de 0 à 5 exigée")
            continue
        if nature not in NATURES:
            erreurs.append(f"{oid}/{critere} : nature {nature!r} hors de {NATURES}")
            continue
        if nature in ("mesuré", "calcul") and not source:
            erreurs.append(f"{oid}/{critere} : une note {nature} exige sa source")
            continue
        verif = c.get("verif")
        if verif is not None and not (isinstance(verif, dict) and ("url" in verif or "fichier" in verif)):
            erreurs.append(f"{oid}/{critere} : verif doit donner une url (et contient) ou un fichier (et cle)")
            verif = None
        o.notes[critere] = Note(critere, note, nature, source, str(c.get("justification") or ""), verif)
    for a in brut.get("arret") or []:
        try:
            arret = Arret(str(a["libelle"]), str(a["indicateur"]), float(a["seuil"]), str(a.get("sens", "min")),
                          str(a["date"]), str(a.get("si_echec") or ""))
            date.fromisoformat(arret.date)
            if arret.sens not in SENS:
                raise ValueError(f"sens {arret.sens!r}")
            if arret.indicateur not in INDICATEURS:
                raise ValueError(f"indicateur {arret.indicateur!r} hors contrat")
        except (KeyError, ValueError, TypeError) as exc:
            erreurs.append(f"{oid} : critère d'arrêt invalide ({exc})")
            continue
        o.arrets.append(arret)
    if o.statut_mere in ("actif", "test") and not o.arrets:
        erreurs.append(f"{oid} : une opportunité active sans critère d'arrêt daté est refusée")
    return o


def charger(chemin: Path) -> tuple[list[Opportunite], dict[str, Any], list[str]]:
    """Charge et valide le portefeuille. Renvoie (opportunités, réglages, erreurs)."""
    erreurs: list[str] = []
    try:
        donnees = tomllib.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [], {}, [f"{chemin} : {exc}"]
    opportunites: list[Opportunite] = []
    vus: set[str] = set()
    for brut in donnees.get("opportunite", []):
        o = _opportunite(brut, erreurs)
        if o is None:
            continue
        if o.id in vus:
            erreurs.append(f"{o.id} : identifiant en double")
            continue
        vus.add(o.id)
        opportunites.append(o)
    return opportunites, dict(donnees.get("reglages") or {}), erreurs
