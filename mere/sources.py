"""Adaptateurs en lecture seule : chaque module garde ses fichiers, la mère les lit sans les modifier.

Un fichier absent ou illisible donne des faits INCONNU, jamais une erreur silencieuse ni un zéro.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .faits import TOUTE_L_ENTREPRISE, Fait
from .statuts import ECHEC, INCONNU, PROUVE

ETAPES_PIPELINE = ("envoi", "relance", "bloque", "reponse", "reponse_positive", "qualifie", "proposition",
                   "gagne", "perdu")
REPONDU = {"reponse", "reponse_positive", "qualifie", "proposition", "gagne", "perdu"}
QUALIFIE = {"qualifie", "proposition", "gagne"}
DATE_FR = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


@dataclass(frozen=True)
class Declaration:
    """Une valeur cumulée déclarée par un module à une date (ex. « 0 € encaissé au 21/11 »)."""

    module: str
    indicateur: str
    valeur: int
    date: str
    source: str


@dataclass(frozen=True)
class Evenement:
    date: str
    opportunite: str
    ref: str
    etape: str
    canal: str
    preuve: str


def _lire(chemin: Path | None) -> str | None:
    if chemin is None or not chemin.is_file():
        return None
    try:
        return chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _date_fr(texte: str) -> str:
    m = DATE_FR.search(texte or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def euros_en_centimes(texte: str) -> int:
    """« 12,50 € » -> 1250. Refuse ce qui n'est pas un montant (lève ValueError)."""
    propre = (texte or "").replace("€", "").replace(" ", "").replace("\xa0", "").replace(" ", "")
    propre = propre.replace(",", ".")
    try:
        valeur = Decimal(propre)
    except InvalidOperation as exc:
        raise ValueError(f"montant illisible : {texte!r}") from exc
    if valeur != valeur.quantize(Decimal("0.01")):
        raise ValueError(f"plus de deux décimales : {texte!r}")
    return int(valeur * 100)


# -- Prévisions et critères d'arrêt (poste business) ----------------------------------------------------

@dataclass(frozen=True)
class Prevision:
    id: str
    date_verdict: str
    libelle: str
    bas: float | None
    central: float | None
    reel: float | None
    sens: str


def lire_previsions(chemin: Path | None) -> list[Prevision] | None:
    texte = _lire(chemin)
    if texte is None:
        return None

    def nombre(v: str) -> float | None:
        v = (v or "").strip().replace(",", ".")
        return float(v) if v else None

    sortie = []
    for ligne in csv.DictReader(io.StringIO(texte), delimiter=";"):
        if not (ligne.get("id") or "").strip():
            continue
        sortie.append(Prevision(ligne["id"].strip(), (ligne.get("date_verdict") or "").strip(),
                                (ligne.get("libelle") or "").strip(), nombre(ligne.get("bas", "")),
                                nombre(ligne.get("central", "")), nombre(ligne.get("reel", "")),
                                (ligne.get("sens") or "plus").strip()))
    return sortie


def faits_verdicts(previsions: list[Prevision] | None, rattachement: dict[str, str], jour: date,
                   source: str) -> list[Fait]:
    """Boucle d'amélioration : une prévision échue sans résultat réel écrit est un ÉCHEC du processus."""
    if previsions is None:
        return [Fait("strat-ge-business", "verdicts_dus", None, INCONNU, source, note="fichier illisible")]
    dus: dict[str, list[Prevision]] = defaultdict(list)
    for p in previsions:
        if p.date_verdict and date.fromisoformat(p.date_verdict) <= jour:
            for cle in (rattachement.get(p.id, TOUTE_L_ENTREPRISE), TOUTE_L_ENTREPRISE):
                dus[cle].append(p)
    faits = []
    for cle in sorted(set(rattachement.values()) | {TOUTE_L_ENTREPRISE}):
        liste = dus.get(cle, [])
        rendus = [p for p in liste if p.reel is not None]
        manquants = [p.id for p in liste if p.reel is None]
        preuve = f"{source} relu le {jour.isoformat()}"
        faits.append(Fait("strat-ge-business", "verdicts_dus", len(liste), PROUVE, source, cle,
                          jour.isoformat(), preuve))
        faits.append(Fait("strat-ge-business", "verdicts_rendus", len(rendus), ECHEC if manquants else PROUVE,
                          source, cle, jour.isoformat(), preuve,
                          note=("verdict non rendu : " + ", ".join(manquants)) if manquants else ""))
    return faits


# -- Statuts déclarés dans les registres des modules ----------------------------------------------------

def lire_tableau_markdown(chemin: Path | None, colonne_cle: int = 0, colonne_valeur: int = 1
                          ) -> dict[str, str] | None:
    """Lignes d'un tableau Markdown : première cellule -> cellule demandée (gras retiré)."""
    texte = _lire(chemin)
    if texte is None:
        return None
    lignes = {}
    for ligne in texte.splitlines():
        if not ligne.startswith("|") or set(ligne.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue
        cellules = [c.strip().replace("**", "") for c in ligne.strip().strip("|").split("|")]
        if len(cellules) > max(colonne_cle, colonne_valeur):
            lignes[cellules[colonne_cle]] = cellules[colonne_valeur]
    return lignes


def normaliser_statut(texte: str) -> str:
    """Statut d'une cellule de registre, lu sur son premier mot significatif (« Gelé (…) », « Actif : … »)."""
    premier = re.split(r"[\s(:;,.]+", (texte or "").strip().lower(), maxsplit=1)[0]
    for prefixe, statut in (("remplac", "arrete"), ("arrêt", "arrete"), ("arret", "arrete"),
                            ("abandon", "arrete"), ("gel", "gele"), ("suspend", "gele"),
                            ("prépar", "en_preparation"), ("prepar", "en_preparation"), ("actif", "actif"),
                            ("test", "test")):
        if premier.startswith(prefixe):
            return statut
    return "inconnu"


# -- Déclarations d'encaissement et de volume des autres modules ----------------------------------------

def declarations_novarys(chemin: Path | None) -> tuple[list[Declaration], list[str]]:
    texte = _lire(chemin)
    if texte is None:
        return [], [f"{chemin} illisible"]
    try:
        donnees = tomllib.loads(texte)
    except tomllib.TOMLDecodeError as exc:
        return [], [f"{chemin} : {exc}"]
    sortie, erreurs = [], []
    for m in donnees.get("measure", []):
        if (m.get("label") or "").lower().startswith("encaiss"):
            try:
                sortie.append(Declaration("novarys", "encaisse_net", euros_en_centimes(m.get("value", "")),
                                          _date_fr(m.get("source", "")), f"{chemin.name} (portail NOVARYS)"))
            except ValueError as exc:
                erreurs.append(str(exc))
    return sortie, erreurs


def declarations_velyx(chemin: Path | None) -> tuple[list[Declaration], list[str]]:
    texte = _lire(chemin)
    if texte is None:
        return [], [f"{chemin} illisible"]
    try:
        kpi = json.loads(texte)
    except ValueError as exc:
        return [], [f"{chemin} : {exc}"]
    sortie, erreurs = [], []
    for cle, indicateur, monetaire in (("encaisse_eur", "encaisse_net", True), ("envois", "prospects_contactes",
                                                                                 False)):
        bloc = kpi.get(cle) or {}
        if bloc.get("valeur") is None:
            continue
        try:
            valeur = euros_en_centimes(str(bloc["valeur"])) if monetaire else int(bloc["valeur"])
        except (ValueError, TypeError) as exc:
            erreurs.append(f"{cle} : {exc}")
            continue
        sortie.append(Declaration("velyx", indicateur, valeur, str(bloc.get("date", ""))[:19],
                                  f"{chemin.name} (VELYX)"))
    return sortie, erreurs


# -- Pipeline commercial (privé) ------------------------------------------------------------------------

def lire_pipeline(chemin: Path | None) -> tuple[list[Evenement] | None, list[str]]:
    texte = _lire(chemin)
    if texte is None:
        return None, []
    evenements, erreurs = [], []
    for n, ligne in enumerate(csv.DictReader(io.StringIO(texte), delimiter=";"), 2):
        etape = (ligne.get("etape") or "").strip()
        try:
            jour = (ligne.get("date") or "").strip()
            date.fromisoformat(jour[:10])
            if etape not in ETAPES_PIPELINE:
                raise ValueError(f"étape inconnue {etape!r}")
            if not (ligne.get("opportunite") or "").strip() or not (ligne.get("ref") or "").strip():
                raise ValueError("opportunité et référence obligatoires")
        except ValueError as exc:
            erreurs.append(f"pipeline ligne {n} : {exc}")
            continue
        evenements.append(Evenement(jour, ligne["opportunite"].strip(), ligne["ref"].strip(), etape,
                                    (ligne.get("canal") or "").strip(), (ligne.get("preuve") or "").strip()))
    return evenements, erreurs


def faits_pipeline(evenements: list[Evenement] | None, opportunites: list[str], source: str) -> list[Fait]:
    if evenements is None:
        return [Fait("pipeline", ind, None, INCONNU, source, note="aucun pipeline lisible")
                for ind in ("prospects_contactes", "reponses", "prospects_qualifies", "conversions")]
    regles = {"prospects_contactes": {"envoi", "relance"}, "envois_bloques": {"bloque"}, "reponses": REPONDU,
              "prospects_qualifies": QUALIFIE, "conversions": {"gagne"}}
    faits = []
    for cle in sorted(set(opportunites) | {e.opportunite for e in evenements} | {TOUTE_L_ENTREPRISE}):
        concernes = [e for e in evenements if cle in (TOUTE_L_ENTREPRISE, e.opportunite)]
        derniere = max((e.date for e in concernes), default="")
        for ind, etapes in regles.items():
            lignes = [e for e in concernes if e.etape in etapes]
            refs = {(e.opportunite, e.ref) for e in lignes}
            sans_preuve = sum(1 for e in lignes if not e.preuve)
            statut = PROUVE if not sans_preuve else INCONNU
            faits.append(Fait("pipeline", ind, len(refs), statut, source, cle, derniere,
                              f"{len(lignes)} ligne(s) de pipeline avec preuve" if statut == PROUVE else "",
                              note=f"{sans_preuve} ligne(s) sans preuve" if sans_preuve else ""))
    return faits


def lire_couts(chemin: Path | None, source: str) -> tuple[list[Fait], list[str]]:
    texte = _lire(chemin)
    if texte is None:
        return [Fait("couts", "couts", None, INCONNU, source, note="aucun journal des coûts", prive=True),
                Fait("couts", "heures", None, INCONNU, source, note="aucun journal des heures")], []
    euros: dict[str, int] = defaultdict(int)
    heures: dict[str, float] = defaultdict(float)
    sans_preuve: dict[str, int] = defaultdict(int)
    erreurs: list[str] = []
    for n, ligne in enumerate(csv.DictReader(io.StringIO(texte), delimiter=";"), 2):
        opp = (ligne.get("opportunite") or TOUTE_L_ENTREPRISE).strip()
        try:
            c = euros_en_centimes(ligne.get("euros") or "0")
            h = float((ligne.get("heures") or "0").replace(",", "."))
            if c < 0 or h < 0:
                raise ValueError("valeur négative")
        except ValueError as exc:
            erreurs.append(f"coûts ligne {n} : {exc}")
            continue
        for cle in {opp, TOUTE_L_ENTREPRISE}:
            euros[cle] += c
            heures[cle] += h
            if not (ligne.get("preuve") or "").strip():
                sans_preuve[cle] += 1
    faits = []
    for cle in sorted(set(euros) | {TOUTE_L_ENTREPRISE}):
        statut = INCONNU if sans_preuve.get(cle) else PROUVE
        preuve = "journal des coûts, chaque ligne avec sa pièce" if statut == PROUVE else ""
        note = f"{sans_preuve[cle]} ligne(s) sans pièce" if sans_preuve.get(cle) else ""
        faits.append(Fait("couts", "couts", euros.get(cle, 0), statut, source, cle, preuve=preuve, note=note,
                          prive=True))
        faits.append(Fait("couts", "heures", round(heures.get(cle, 0.0), 2), statut, source, cle, preuve=preuve,
                          note=note))
    return faits, erreurs


# -- Rejeu des suites de tests des modules --------------------------------------------------------------

VARIABLES_GARDEES = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
                     "https_proxy", "http_proxy", "no_proxy", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE",
                     "NODE_EXTRA_CA_CERTS", "UV_CACHE_DIR"}
MOTS_SECRETS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CLE", "PASS")


def environnement_propre() -> dict[str, str]:
    """Environnement du rejeu : liste blanche, aucune variable dont le nom évoque un secret."""
    return {k: v for k, v in os.environ.items()
            if k in VARIABLES_GARDEES and not any(m in k.upper() for m in MOTS_SECRETS)}


def _git(depot: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(depot), *args], capture_output=True, text=True, timeout=30,
                              check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def rejouer(nom: str, depot: Path | None, commande: list[str], bilan: str, delai: int = 900) -> dict[str, Any]:
    """Exécute la suite d'un module. Réussi = code 0 ET ligne de bilan vue ; sinon pas PROUVÉ."""
    quand = datetime.now(UTC).isoformat(timespec="seconds")
    if depot is None or not depot.is_dir():
        return {"nom": nom, "date": quand, "code": None, "statut": INCONNU, "bilan": "", "commit": "",
                "note": "dépôt absent de cette machine"}
    avant = _git(depot, "status", "--porcelain")
    try:
        fini = subprocess.run(commande, cwd=depot, env=environnement_propre(), capture_output=True, text=True,
                              timeout=delai, check=False)
        sortie, code = (fini.stdout or "") + (fini.stderr or ""), fini.returncode
    except subprocess.TimeoutExpired:
        sortie, code = "", -1
    except OSError as exc:
        sortie, code = str(exc), -2
    lignes = [ligne.strip() for ligne in sortie.splitlines() if re.search(bilan, ligne)]
    vu = lignes[-1][:200] if lignes else ""
    statut = ECHEC if code != 0 else (PROUVE if vu else INCONNU)
    apres = _git(depot, "status", "--porcelain")
    note = "" if vu or code != 0 else "code 0 sans ligne de bilan : non vérifié"
    if apres != avant:
        # La mère lit les modules sans les modifier : un rejeu qui écrit dans le dépôt ne prouve rien.
        statut, note = (ECHEC if statut == ECHEC else INCONNU), "le rejeu a modifié le dépôt du module"
    return {"nom": nom, "date": quand, "code": code, "statut": statut, "bilan": vu,
            "commit": _git(depot, "rev-parse", "HEAD")[:12], "propre": apres == "", "note": note}


def faits_rejeux(resultats: list[dict[str, Any]], depots: dict[str, Path | None],
                 rattachement: dict[str, list[str]]) -> list[Fait]:
    """Un rejeu ne prouve que le commit sur lequel il a tourné : autre commit ou dépôt modifié => INCONNU.
    Chaque rejeu donne un fait pour le module (« module:<nom> ») et un par opportunité rattachée."""
    faits = []
    for r in resultats:
        depot = depots.get(r["nom"])
        actuel = _git(depot, "rev-parse", "HEAD")[:12] if depot else ""
        statut, note = r["statut"], r.get("note", "")
        if statut == PROUVE and (not actuel or actuel != r.get("commit") or not r.get("propre", False)):
            statut, note = INCONNU, f"rejoué sur {r.get('commit') or '?'}, dépôt maintenant à {actuel or '?'}"
        valeur = None if statut == INCONNU else statut == PROUVE
        preuve = f"{r.get('commit')} · {r.get('bilan')}" if statut == PROUVE else ""
        for cle in [f"module:{r['nom']}", *rattachement.get(r["nom"], [])]:
            faits.append(Fait(f"rejeu:{r['nom']}", "suite_verte", valeur, statut, f"rejeu de la suite de {r['nom']}",
                              cle, r["date"], preuve, note))
    return faits


def activite_recente(evenements: list[Evenement] | None, jour: date, jours: int = 14) -> dict[str, int]:
    """Nombre d'envois et de relances par opportunité sur les `jours` derniers jours."""
    limite = jour - timedelta(days=jours)
    compte: dict[str, int] = defaultdict(int)
    for e in evenements or []:
        if e.etape in ("envoi", "relance") and date.fromisoformat(e.date[:10]) >= limite:
            compte[e.opportunite] += 1
    return dict(compte)
