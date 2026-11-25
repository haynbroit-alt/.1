"""Expérience numérique : où le refroidissement radiatif échoue, et quel levier compte vraiment.

Usage : python3 experience.py   (imprime les tableaux de RESULTATS.md)
"""
from modele import Ciel, Surface, puissance_radiative_nette, temperature_equilibre

K = 273.15
SOLEIL_MIDI = 900.0   # W/m², ciel clair, soleil haut (hypothèse de calcul)

CLIMATS = [
    ("Désert sec", 38, 2),
    ("Tempéré, été", 26, 12),
    ("Méditerranéen, été", 32, 16),
    ("Tropical humide", 32, 24),
    ("Équatorial très humide (extrapolé)", 31, 26),
]

PEINTURE = Surface("Peinture blanche « fraîche »", 0.95, 0.95, 0.05, 90.0)


def ligne_climat(nom, t_air_c, rosee):
    ciel = Ciel(t_air_c + K, rosee)
    p_nuit = puissance_radiative_nette(PEINTURE, ciel, ciel.t_air)
    dt_nuit = temperature_equilibre(PEINTURE, ciel, 0.0, 8.0) - ciel.t_air
    dt_midi = temperature_equilibre(PEINTURE, ciel, SOLEIL_MIDI, 8.0) - ciel.t_air
    note = "" if ciel.dans_le_domaine_valide else " (hors domaine)"
    return (f"| {nom}{note} | {t_air_c} | {rosee} | {ciel.emissivite_totale:.3f} | {ciel.t0:.2f} | "
            f"{p_nuit:.0f} | {dt_nuit:+.1f} | {dt_midi:+.1f} |")


def leviers(t_air_c=32, rosee=24, h_base=8.0):
    ciel = Ciel(t_air_c + K, rosee)
    cas = [
        ("Base : peinture blanche (soleil absorbé 5 %, convection h = 8)", PEINTURE, h_base),
        ("Soleil absorbé 5 % → 1 % (meilleurs films de labo)",
         Surface("", 0.95, 0.95, 0.01, 90.0), h_base),
        ("Émission limitée à la fenêtre 8–13 µm (sélectivité spectrale)",
         Surface("", 0.95, 0.05, 0.05, 90.0), h_base),
        ("Écran angulaire : échange limité à 45° du zénith (avec sélectivité)",
         Surface("", 0.95, 0.05, 0.05, 45.0), h_base),
        ("Écran contre l'air : h = 8 → 2 (film transparent à l'infrarouge)", PEINTURE, 2.0),
        ("Isolation très forte : h = 8 → 0,5", PEINTURE, 0.5),
        ("Tout combiné sans écran angulaire : 1 %, sélectif, h = 0,5",
         Surface("", 0.95, 0.05, 0.01, 90.0), 0.5),
        ("Tout combiné avec écran angulaire à 45°",
         Surface("", 0.95, 0.05, 0.01, 45.0), 0.5),
    ]
    base = temperature_equilibre(PEINTURE, ciel, SOLEIL_MIDI, h_base) - ciel.t_air
    lignes = []
    for libelle, s, h in cas:
        dt = temperature_equilibre(s, ciel, SOLEIL_MIDI, h) - ciel.t_air
        p = puissance_radiative_nette(s, ciel, ciel.t_air) - s.absorption_solaire * SOLEIL_MIDI
        lignes.append(f"| {libelle} | {p:.0f} | {dt:+.1f} | {dt - base:+.1f} |")
    return ciel, lignes


if __name__ == "__main__":
    print("Tableau 1. Peinture blanche « fraîche » (ε = 0,95, 5 % du soleil absorbé, convection h = 8 W/m²/K)\n")
    print("| Climat | Air (°C) | Rosée (°C) | Émissivité du ciel | Transmittance zénithale 8–13 µm | "
          "Puissance de nuit à l'ambiante (W/m²) | Écart de nuit (°C) | Écart à midi (°C) |")
    print("|---|---|---|---|---|---|---|---|")
    for c in CLIMATS:
        print(ligne_climat(*c))
    ciel, lignes = leviers()
    print(f"\nTableau 2. Climat tropical humide (air 32 °C, rosée 24 °C), midi, soleil {SOLEIL_MIDI:.0f} W/m²\n")
    print("| Levier, changé seul | Puissance nette à l'ambiante (W/m²) | Écart à l'air (°C) | Gain sur la base (°C) |")
    print("|---|---|---|---|")
    for lg in lignes:
        print(lg)
    print(f"\nTableau 3. Seuil solaire : part maximale du soleil absorbé ({SOLEIL_MIDI:.0f} W/m²) au-delà de laquelle "
          "aucune surface ε = 0,95 ne peut rester sous la température de l'air à midi\n")
    print("| Climat | Seuil d'absorption solaire | Réflexion solaire minimale |")
    print("|---|---|---|")
    for nom, t_air_c, rosee in CLIMATS:
        ciel = Ciel(t_air_c + K, rosee)
        seuil = puissance_radiative_nette(PEINTURE, ciel, ciel.t_air) / SOLEIL_MIDI
        print(f"| {nom} | {seuil:.1%} | {1 - seuil:.1%} |")
    print("\nTableau 4. Écran angulaire (sélectif, 1 % absorbé, h = 0,5), tropical humide : écart à l'air selon le cône\n")
    print("| Demi-angle du cône | Écart à l'air à midi (°C) |")
    print("|---|---|")
    ciel = Ciel(32 + K, 24)  # tropical humide (ne pas réutiliser le dernier climat de la boucle précédente)
    for angle in (90, 75, 60, 45, 30):
        s = Surface("", 0.95, 0.05, 0.01, float(angle))
        print(f"| {angle}° | {temperature_equilibre(s, ciel, SOLEIL_MIDI, 0.5) - ciel.t_air:+.1f} |")
