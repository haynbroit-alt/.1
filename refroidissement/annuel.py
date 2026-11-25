"""Étape 3 : le froid rayonné réellement disponible sur une année, nuages compris.

Données : NASA POWER, horaire, année 2024 (UTC). Chaque heure donne :
- la température de l'air et le point de rosée à 2 m ;
- le soleil reçu par une surface horizontale (W/m², moyenne de l'heure) ;
- le rayonnement infrarouge que le ciel envoie vers le sol, avec les nuages réels (« tous ciels ») et
  sans nuages (« ciel clair »).

Pour une surface grise d'émissivité ε, à la température de l'air, le bilan est exact, sans modèle de ciel :
    P = ε (σ Ta⁴ − L_ciel) − α · Soleil
L_ciel vient des données. Les nuages sont donc pris en compte tels que les estime la NASA, et non par une formule.

Usage :
    python3 annuel.py                 # lit donnees/nasa_power_2024.csv.gz et imprime les tableaux
    python3 annuel.py --telecharger   # retélécharge les données depuis NASA POWER (gratuit, sans clé)

Données : NASA Langley Research Center (LaRC) POWER Project, financé par le programme NASA Earth Science/Applied
Science. Ce sont des estimations par réanalyse et par satellite, pas des mesures de station.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from modele import SIGMA, emissivite_berdahl_martin

K = 273.15
EPS = 0.95
FICHIER = Path(__file__).with_name("donnees") / "nasa_power_2024.csv.gz"
VILLES = [  # nom, latitude, longitude, catégorie
    ("Singapour", 1.29, 103.85, "humide"),
    ("Jakarta", -6.21, 106.85, "humide"),
    ("Lagos", 6.45, 3.39, "humide"),
    ("Bangkok", 13.75, 100.50, "humide"),
    ("Bombay", 19.08, 72.88, "humide"),
    ("Séville", 37.39, -5.98, "référence"),
    ("Riyad", 24.71, 46.68, "référence"),
    ("Phoenix", 33.45, -112.07, "référence"),
]
PARAMS = "T2M,T2MDEW,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_LW_DWN,CLRSKY_SFC_LW_DWN"


@dataclass(frozen=True)
class Heure:
    t_air_c: float
    rosee_c: float
    soleil: float      # W/m²
    ciel_tous: float   # W/m², nuages compris
    ciel_clair: float  # W/m², sans nuages


def puissance(h: Heure, absorption: float, ciel: float | None = None, eps: float = EPS) -> float:
    """Puissance nette (W/m²) d'une surface grise à la température de l'air ; positive = elle refroidit."""
    l_ciel = h.ciel_tous if ciel is None else ciel
    return eps * (SIGMA * (h.t_air_c + K) ** 4 - l_ciel) - absorption * h.soleil


def froid_annuel(heures: list[Heure], absorption: float, clair: bool = False, filtre=None) -> float:
    """Somme sur l'année du froid disponible à la température de l'air (kWh/m²), heures sélectionnées par filtre."""
    total = 0.0
    for h in heures:
        if filtre is not None and not filtre(h):
            continue
        p = puissance(h, absorption, h.ciel_clair if clair else None)
        if p > 0:
            total += p  # chaque valeur couvre une heure : W·h
    return total / 1000


def part_heures_ensoleillees_sous_ambiante(heures: list[Heure], absorption: float, seuil_soleil: float = 300) -> float:
    """Part des heures bien ensoleillées où la surface peut descendre sous la température de l'air."""
    soleil = [h for h in heures if h.soleil >= seuil_soleil]
    if not soleil:
        return 0.0
    return sum(1 for h in soleil if puissance(h, absorption) > 0) / len(soleil)


def ecart_ciel_clair(heures: list[Heure]) -> tuple[float, float, float]:
    """Compare le ciel clair de Berdahl et Martin (étapes 1 et 2) au ciel clair de la NASA.

    Renvoie (écart moyen en W/m², écart moyen en % du flux NASA, part des heures hors du domaine de calage).
    """
    ecarts, relatifs, hors = [], [], 0
    for h in heures:
        modele = emissivite_berdahl_martin(h.rosee_c) * SIGMA * (h.t_air_c + K) ** 4
        ecarts.append(modele - h.ciel_clair)
        relatifs.append((modele - h.ciel_clair) / h.ciel_clair)
        hors += not (-13 <= h.rosee_c <= 24)
    n = len(heures)
    return sum(ecarts) / n, sum(relatifs) / n, hors / n


def decale_ciel(heures: list[Heure], delta: float) -> list[Heure]:
    """Même année, avec un rayonnement du ciel décalé de delta W/m² (test de sensibilité aux biais des données)."""
    return [Heure(h.t_air_c, h.rosee_c, h.soleil, h.ciel_tous + delta, h.ciel_clair + delta) for h in heures]


def telecharger(dossier: Path = FICHIER.parent) -> None:
    """Retélécharge l'année 2024 de chaque ville depuis NASA POWER et écrit le CSV compressé."""
    lignes = []
    for nom, lat, lon, _ in VILLES:
        url = ("https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=" + PARAMS +
               f"&community=RE&longitude={lon}&latitude={lat}&start=20240101&end=20241231&format=JSON"
               "&time-standard=UTC")
        with urllib.request.urlopen(url, timeout=180) as r:
            p = json.load(r)["properties"]["parameter"]
        for cle in sorted(p["T2M"]):
            lignes.append([nom, cle] + [p[x][cle] for x in PARAMS.split(",")])
        time.sleep(2)
    dossier.mkdir(exist_ok=True)
    with gzip.open(FICHIER, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ville", "heure_utc"] + PARAMS.split(","))
        w.writerows(lignes)


def charger(fichier: Path = FICHIER) -> dict[str, list[Heure]]:
    """Lit le CSV compressé ; ignore les heures dont une valeur manque (-999)."""
    villes: dict[str, list[Heure]] = {}
    with gzip.open(fichier, "rt", encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            v = [float(ligne[x]) for x in PARAMS.split(",")]
            if -999.0 in v:
                continue
            villes.setdefault(ligne["ville"], []).append(Heure(*v))
    return villes


def rapport(villes: dict[str, list[Heure]]) -> str:
    out = io.StringIO()
    p = lambda *a: print(*a, file=out)  # noqa: E731
    absorptions = (0.10, 0.05, 0.03, 0.01)

    p("Tableau 5. Contrôle du modèle de ciel clair des étapes 1 et 2 (Berdahl et Martin) contre la NASA, 2024\n")
    p("| Ville | Rosée moyenne (°C) | Heures hors du domaine de calage | Écart moyen (W/m²) | Écart moyen (%) |")
    p("|---|---|---|---|---|")
    for nom, *_ in VILLES:
        hs = villes[nom]
        b, r, hors = ecart_ciel_clair(hs)
        rosee = sum(h.rosee_c for h in hs) / len(hs)
        p(f"| {nom} | {rosee:.1f} | {hors:.0%} | {b:+.1f} | {r:+.1%} |")

    p("\nTableau 6. Froid disponible sur l'année à la température de l'air (kWh/m²/an), nuages compris, "
      "selon la part du soleil absorbée\n")
    p("| Ville | " + " | ".join(f"{a:.0%} absorbé" for a in absorptions) +
      " | Dont la nuit (toute surface) | Sans nuages, 3 % absorbé |")
    p("|---|" + "---|" * (len(absorptions) + 2))
    for nom, *_ in VILLES:
        hs = villes[nom]
        jour = [froid_annuel(hs, a) for a in absorptions]
        nuit = froid_annuel(hs, 0.0, filtre=lambda h: h.soleil < 5)
        clair = froid_annuel(hs, 0.03, clair=True)
        p(f"| {nom} | " + " | ".join(f"{x:.0f}" for x in jour) + f" | {nuit:.0f} | {clair:.0f} |")

    p("\nTableau 7. Part des heures bien ensoleillées (≥ 300 W/m²) où une surface peut rester sous la "
      "température de l'air, nuages compris\n")
    p("| Ville | " + " | ".join(f"{a:.0%} absorbé" for a in absorptions) + " |")
    p("|---|" + "---|" * len(absorptions))
    for nom, *_ in VILLES:
        hs = villes[nom]
        p(f"| {nom} | " + " | ".join(f"{part_heures_ensoleillees_sous_ambiante(hs, a):.0%}" for a in absorptions)
          + " |")

    p("\nTableau 8. Sensibilité : froid annuel (kWh/m²/an, 3 % absorbé) si le rayonnement du ciel estimé par la NASA "
      "est faux de ±10 W/m² (environ ±2 %)\n")
    p("| Ville | Ciel −10 W/m² | Données | Ciel +10 W/m² | Variation |")
    p("|---|---|---|---|---|")
    for nom, *_ in VILLES:
        hs = villes[nom]
        bas, mid, haut = (froid_annuel(decale_ciel(hs, d), 0.03) for d in (-10.0, 0.0, 10.0))
        p(f"| {nom} | {bas:.0f} | {mid:.0f} | {haut:.0f} | ±{(bas - haut) / 2 / mid:.0%} |")
    return out.getvalue()


if __name__ == "__main__":
    if "--telecharger" in sys.argv:
        telecharger()
    print(rapport(charger()), end="")
