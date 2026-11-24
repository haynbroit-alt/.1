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

ETAPES_PIPELINE = ("envoi", "relance", "bloque", "rebond", "reponse", "reponse_positive", "refus", "qualifie",
                   "proposition", "gagne", "perdu")
# « perdu » clôt un prospect sans dire qu'il a répondu ; « refus » est une réponse négative explicite.
REPONDU = {"reponse", "reponse_positive", "refus", "qualifie", "proposition", "gagne"}
QUALIFIE = {"qualifie", "proposition", "gagne"}
DATE_FR = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


@dataclass(frozen=True)
class Declaration:
    """Une valeur cumulée déclarée par un module à une date (ex. « 0 € encaissé au 21/11 »).
    `perimetre` : « * » si la valeur couvre toute l'entreprise, sinon le module dont elle ne couvre que l'activité."""

    module: str
    indicateur: str
    valeur: int
    date: str
    source: str
    perimetre: str = "*"


@dataclass(frozen=True)
class Evenement:
    date: str
    opportunite: str
    ref: str
    etape: str
    canal: str
    preuve: str
    domaine: str = ""


def _lire(chemin: Path | None) -> str | None:
    if chemin is None or not chemin.is_file():
        return None
    try:
        return chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def instant(texte: str) -> datetime | None:
    """Instant UTC d'une date ISO (« T » ou espace, avec ou sans fuseau ; sans fuseau = UTC).
    Une date seule (sans heure) renvoie None : l'heure n'est pas connue."""
    t = (texte or "").strip().replace("Z", "+00:00")
    if len(t) <= 10:
        return None
    try:
        d = datetime.fromisoformat(t.replace(" ", "T", 1))
    except ValueError:
        return None
    return d.replace(tzinfo=UTC) if d.tzinfo is None else d.astimezone(UTC)


def jour_de(texte: str) -> date | None:
    """Jour UTC d'une date ou d'un instant ISO ; None si illisible."""
    i = instant(texte)
    if i is not None:
        return i.date()
    try:
        return date.fromisoformat((texte or "").strip()[:10])
    except ValueError:
        return None


def _date_fr(texte: str) -> str:
    m = DATE_FR.search(texte or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def euros_en_centimes(texte: str) -> int:
    """« 12,50 € » -> 1250. Refuse ce qui n'est pas un montant (lève ValueError)."""
    propre = (texte or "").replace("€", "").replace(" ", "").replace("\xa0", "").replace(" ", "")
    propre = propre.replace(",", ".")
    try:
        if not re.fullmatch(r"-?\d+(?:\.\d{1,2})?", propre):
            raise InvalidOperation  # ni exposant, ni infini, ni plus de deux décimales
        valeur = Decimal(propre)
        if not valeur.is_finite() or valeur != valeur.quantize(Decimal("0.01")):
            raise InvalidOperation
    except (InvalidOperation, ValueError) as exc:
        # Le contenu de la cellule n'est jamais recopié dans le message : il peut être privé.
        raise ValueError("montant illisible ou à plus de deux décimales") from exc
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
    haut: float | None = None


def lire_previsions(chemin: Path | None, erreurs: list[str] | None = None,
                    rejetees: list[str] | None = None) -> list[Prevision] | None:
    """Prévisions du poste business. Une ligne illisible est rejetée et signalée, jamais devinée."""
    texte = _lire(chemin)
    if texte is None:
        return None

    def nombre(v: str) -> float | None:
        v = (v or "").strip().replace(",", ".")
        if not v:
            return None
        x = float(v)
        if x != x or x in (float("inf"), float("-inf")):
            raise ValueError("nombre non fini")
        return x

    sortie = []
    for n, ligne in enumerate(csv.DictReader(io.StringIO(texte.lstrip("\ufeff")), delimiter=";"), 2):
        if not (ligne.get("id") or "").strip():
            continue
        try:
            jour = (ligne.get("date_verdict") or "").strip()
            date.fromisoformat(jour)
            sens = (ligne.get("sens") or "plus").strip()
            if sens not in ("plus", "moins"):
                raise ValueError("sens attendu : plus ou moins")
            p = Prevision(ligne["id"].strip(), jour, (ligne.get("libelle") or "").strip(), nombre(ligne.get("bas", "")),
                          nombre(ligne.get("central", "")), nombre(ligne.get("reel", "")), sens,
                          nombre(ligne.get("haut", "")))
        except ValueError:
            if erreurs is not None:
                erreurs.append(f"prévisions ligne {n} : date, nombre ou sens illisible")
            if rejetees is not None:
                rejetees.append(ligne["id"].strip())
            continue
        sortie.append(p)
    return sortie


def faits_verdicts(previsions: list[Prevision] | None, rattachement: dict[str, str], jour: date,
                   source: str, rejetees: list[str] | None = None) -> list[Fait]:
    """Boucle d'amélioration : une prévision échue sans résultat réel écrit est un ÉCHEC du processus. Une prévision
    illisible n'est pas une prévision absente : l'opportunité qu'elle concerne passe en INCONNU."""
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
        illisibles = [pid for pid in rejetees or [] if cle in (TOUTE_L_ENTREPRISE, rattachement.get(pid))]
        statut = ECHEC if manquants else (INCONNU if illisibles else PROUVE)
        notes = [("verdict non rendu : " + ", ".join(manquants)) if manquants else "",
                 ("prévision illisible : " + ", ".join(illisibles)) if illisibles else ""]
        faits.append(Fait("strat-ge-business", "verdicts_rendus", len(rendus) if statut != INCONNU else None, statut,
                          source, cle, jour.isoformat(), preuve if statut == PROUVE else "",
                          note="; ".join(n for n in notes if n)))
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
    """Statut d'une cellule de registre, lu dans sa première proposition (avant « : », « ; », « ( », « , »).
    « En préparation », « En pause », « Inactif », « Gelé (…) », « Actif : … » sont reconnus ; une description
    (« Site non mis en ligne, lien A_REMPLACER ») ne l'est pas."""
    clause = re.split(r"[:;(,—–]", (texte or "").strip().lower(), maxsplit=1)[0]
    mots = re.findall(r"[a-zàâçéèêëîïôûùüÿœ]+", clause)
    if any(m in ("pas", "non", "jamais") for m in mots) and any(m.startswith("actif") for m in mots):
        return "en_preparation"  # « Pas encore actif », « non actif »
    regles = (("inactif", "gele"), ("désactiv", "gele"), ("desactiv", "gele"), ("pause", "gele"), ("veille", "gele"),
              ("gel", "gele"), ("suspend", "gele"), ("remplac", "arrete"), ("arrêt", "arrete"), ("arret", "arrete"),
              ("stopp", "arrete"), ("archiv", "arrete"), ("abandon", "arrete"), ("clos", "arrete"),
              ("prépar", "en_preparation"), ("prepar", "en_preparation"), ("test", "test"), ("actif", "actif"))
    for prefixe, statut in regles:
        if any(m.startswith(prefixe) for m in mots):
            return statut
    return "inconnu"


# -- Déclarations d'encaissement et de volume des autres modules ----------------------------------------

def declarations_novarys(chemin: Path | None) -> tuple[list[Declaration], list[str]]:
    """Mesure « Encaissé » du portail NOVARYS. Par construction, le portail affiche l'encaissé de tout l'écosystème
    (« registre de VELYX et moteur ») : il est comparé au total de l'entreprise, pas à un seul module."""
    texte = _lire(chemin)
    if texte is None:
        return [], []  # source absente : rien de déclaré, ce n'est pas une erreur de lecture
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
                erreurs.append(f"mesure « Encaissé » : {exc}")
    return sortie, erreurs


def declarations_velyx(chemin: Path | None) -> tuple[list[Declaration], list[str]]:
    texte = _lire(chemin)
    if texte is None:
        return [], []  # source absente : rien de déclaré, ce n'est pas une erreur de lecture
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
        except (ValueError, TypeError):
            erreurs.append(f"{cle} : valeur illisible")
            continue
        sortie.append(Declaration("velyx", indicateur, valeur, str(bloc.get("date", "")), f"{chemin.name} (VELYX)",
                                  perimetre="velyx"))
    return sortie, erreurs


# -- Pipeline commercial (privé) ------------------------------------------------------------------------

def lire_pipeline(chemin: Path | None) -> tuple[list[Evenement] | None, list[str]]:
    texte = _lire(chemin)
    if texte is None:
        return None, []
    evenements, erreurs = [], []
    for n, ligne in enumerate(csv.DictReader(io.StringIO(texte.lstrip("\ufeff")), delimiter=";"), 2):
        etape = (ligne.get("etape") or "").strip()
        jour = (ligne.get("date") or "").strip()
        # Les messages ne recopient jamais le contenu d'une cellule : il peut être nominatif.
        if jour_de(jour) is None or (len(jour) > 10 and instant(jour) is None):
            erreurs.append(f"pipeline ligne {n} : date illisible (AAAA-MM-JJ ou AAAA-MM-JJTHH:MM attendu)")
            continue
        if etape not in ETAPES_PIPELINE:
            erreurs.append(f"pipeline ligne {n} : étape hors liste {ETAPES_PIPELINE}")
            continue
        if not (ligne.get("opportunite") or "").strip() or not (ligne.get("ref") or "").strip():
            erreurs.append(f"pipeline ligne {n} : opportunité et référence obligatoires")
            continue
        evenements.append(Evenement(jour, ligne["opportunite"].strip(), ligne["ref"].strip(), etape,
                                    (ligne.get("canal") or "").strip(), (ligne.get("preuve") or "").strip(),
                                    (ligne.get("domaine") or "").strip().lower()))
    return evenements, erreurs


def faits_pipeline(evenements: list[Evenement] | None, opportunites: list[str], source: str,
                   rejetees: int) -> list[Fait]:
    """Comptes du pipeline. Une ligne rejetée peut être un envoi ou une réponse manquante : tant qu'il en reste,
    aucun compte n'est PROUVÉ."""
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
            statut = PROUVE if not sans_preuve and not rejetees else INCONNU
            notes = [f"{sans_preuve} ligne(s) sans preuve" if sans_preuve else "",
                     f"{rejetees} ligne(s) rejetée(s) à la lecture" if rejetees else ""]
            faits.append(Fait("pipeline", ind, len(refs), statut, source, cle, derniere,
                              f"{len(lignes)} ligne(s) de pipeline avec preuve" if statut == PROUVE else "",
                              note="; ".join(n for n in notes if n)))
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
    for n, ligne in enumerate(csv.DictReader(io.StringIO(texte.lstrip("\ufeff")), delimiter=";"), 2):
        opp = (ligne.get("opportunite") or TOUTE_L_ENTREPRISE).strip()
        try:
            c = euros_en_centimes(ligne.get("euros") or "0")
            h = float((ligne.get("heures") or "0").replace(",", "."))
            if c < 0 or not 0 <= h < float("inf"):
                raise ValueError
        except ValueError:
            erreurs.append(f"coûts ligne {n} : montant ou heures illisibles, négatifs ou infinis")
            # Une ligne illisible est un coût inconnu : le total ne peut plus être prouvé.
            for cle in {opp, TOUTE_L_ENTREPRISE}:
                sans_preuve[cle] += 1
            continue
        for cle in {opp, TOUTE_L_ENTREPRISE}:
            euros[cle] += c
            heures[cle] += h
            if not (ligne.get("preuve") or "").strip():
                sans_preuve[cle] += 1
    faits = []
    for cle in sorted(set(euros) | set(sans_preuve) | {TOUTE_L_ENTREPRISE}):
        statut = INCONNU if sans_preuve.get(cle) else PROUVE
        preuve = "journal des coûts, chaque ligne avec sa pièce" if statut == PROUVE else ""
        note = f"{sans_preuve[cle]} ligne(s) sans pièce ou illisible(s)" if sans_preuve.get(cle) else ""
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


def faits_rejeux(controles_suites: list[Any], rattachement: dict[str, list[str]]) -> list[Fait]:
    """Faits « suite verte » tirés des contrôles en clone propre (voir controles.rejouer_propre).
    Chaque contrôle donne un fait pour le module (« module:<nom> ») et un par opportunité rattachée."""
    faits = []
    for c in controles_suites:
        nom = c.id.split(":", 1)[1]
        valeur = None if c.statut in (INCONNU, "CONFLIT") else c.statut == PROUVE
        preuve = f"{c.reference} · {c.detail}" if c.statut == PROUVE else ""
        for cle in [f"module:{nom}", *rattachement.get(nom, [])]:
            faits.append(Fait(c.controleur, "suite_verte", valeur, c.statut, f"suite de {nom} rejouée par la mère",
                              cle, c.date, preuve, "" if c.statut == PROUVE else c.detail))
    return faits


def activite_recente(evenements: list[Evenement] | None, jour: date, jours: int = 14) -> dict[str, int]:
    """Nombre d'envois et de relances par opportunité sur les `jours` derniers jours."""
    limite = jour - timedelta(days=jours)
    compte: dict[str, int] = defaultdict(int)
    for e in evenements or []:
        jour_e = jour_de(e.date)
        if e.etape in ("envoi", "relance") and jour_e is not None and jour_e >= limite:
            compte[e.opportunite] += 1
    return dict(compte)
