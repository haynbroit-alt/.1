"""Prédiction enregistrée AVANT l'expérience de l'étape 4 : écart de température entre des échantillons blancs.

Conditions supposées (hypothèses, à remplacer par les mesures du jour) : midi d'hiver ensoleillé dans le sud de la
France, air 12 °C, point de rosée 4 °C, soleil 500 W/m² ; échantillon posé sur une boîte isolante, avec ou sans film
alimentaire (polyéthylène, transparent à l'infrarouge) contre le vent. Usage : python3 prediction_experience.py
"""
from modele import Ciel, Surface, temperature_equilibre

K = 273.15
CIEL = Ciel(12 + K, 4)
SOLEIL = 500.0
ECHANTILLONS = [
    ("Peinture blanche ordinaire (≈ 10 % absorbé)", 0.10),
    ("Blanc « frais » (≈ 5 % absorbé)", 0.05),
    ("Cible : blanc à 97 % (3 % absorbé)", 0.03),
]

if __name__ == "__main__":
    print(f"Ciel : émissivité {CIEL.emissivite_totale:.3f}, domaine valide : {CIEL.dans_le_domaine_valide}\n")
    print("| Échantillon | Écart à l'air, sans film, h = 8 (°C) | Écart à l'air, avec film, h = 4 (°C) | Nuit, avec film (°C) |")
    print("|---|---|---|---|")
    for nom, a in ECHANTILLONS:
        s = Surface(nom, 0.95, 0.95, a, 90.0)
        d8 = temperature_equilibre(s, CIEL, SOLEIL, 8.0) - CIEL.t_air
        d4 = temperature_equilibre(s, CIEL, SOLEIL, 4.0) - CIEL.t_air
        n4 = temperature_equilibre(s, CIEL, 0.0, 4.0) - CIEL.t_air
        print(f"| {nom} | {d8:+.1f} | {d4:+.1f} | {n4:+.1f} |")
