"""Tests de l'analyse annuelle, sur des heures fabriquées dont on connaît la réponse."""
import gzip
import tempfile
import unittest
from pathlib import Path

from annuel import (EPS, Heure, charger, ecart_ciel_clair, froid_annuel, part_heures_ensoleillees_sous_ambiante,
                    puissance)
from modele import SIGMA, emissivite_berdahl_martin

K = 273.15


class Bilan(unittest.TestCase):
    def test_puissance_surface_grise(self):
        h = Heure(30.0, 20.0, 0.0, 400.0, 380.0)
        self.assertAlmostEqual(puissance(h, 0.05), EPS * (SIGMA * (30 + K) ** 4 - 400.0), places=9)

    def test_soleil_retranche(self):
        h = Heure(30.0, 20.0, 1000.0, 400.0, 380.0)
        self.assertAlmostEqual(puissance(h, 0.0) - puissance(h, 0.05), 50.0, places=9)

    def test_ciel_clair_utilise_si_demande(self):
        h = Heure(30.0, 20.0, 0.0, 400.0, 380.0)
        self.assertAlmostEqual(puissance(h, 0.0, h.ciel_clair) - puissance(h, 0.0), EPS * 20.0, places=9)


class Agregats(unittest.TestCase):
    def setUp(self):
        s = SIGMA * (30 + K) ** 4
        # Une heure de nuit à +95 W/m² (ciel 100 W/m² sous σT⁴), une heure ensoleillée qui chauffe, une neutre.
        self.heures = [Heure(30.0, 20.0, 0.0, s - 100, s - 120),
                       Heure(30.0, 20.0, 800.0, s - 100, s - 120),
                       Heure(30.0, 20.0, 0.0, s, s)]

    def test_seules_les_heures_qui_refroidissent_comptent(self):
        # nuit : 0,95 × 100 = 95 Wh ; jour : 95 - 0,05 × 800 = 55 Wh ; neutre : 0
        self.assertAlmostEqual(froid_annuel(self.heures, 0.05), (95 + 55) / 1000, places=9)
        # Avec 20 % absorbé, l'heure de jour réchauffe (95 - 160 < 0) : elle ne compte pas.
        self.assertAlmostEqual(froid_annuel(self.heures, 0.20), 95 / 1000, places=9)

    def test_filtre_nuit(self):
        self.assertAlmostEqual(froid_annuel(self.heures, 0.05, filtre=lambda h: h.soleil < 5), 95 / 1000, places=9)

    def test_part_ensoleillee(self):
        self.assertEqual(part_heures_ensoleillees_sous_ambiante(self.heures, 0.05), 1.0)
        self.assertEqual(part_heures_ensoleillees_sous_ambiante(self.heures, 0.20), 0.0)


class Sensibilite(unittest.TestCase):
    def test_ciel_plus_chaud_moins_de_froid(self):
        from annuel import decale_ciel
        s = SIGMA * (30 + K) ** 4
        hs = [Heure(30.0, 20.0, 0.0, s - 100, s - 120)]
        self.assertAlmostEqual(froid_annuel(decale_ciel(hs, 10.0), 0.0), EPS * 90 / 1000, places=9)


class Donnees(unittest.TestCase):
    def test_ecart_nul_si_nasa_egale_le_modele(self):
        modele = emissivite_berdahl_martin(20.0) * SIGMA * (30 + K) ** 4
        b, r, hors = ecart_ciel_clair([Heure(30.0, 20.0, 0.0, 0.0, modele)])
        self.assertAlmostEqual(b, 0.0, places=9)
        self.assertAlmostEqual(r, 0.0, places=9)
        self.assertEqual(hors, 0.0)

    def test_valeurs_manquantes_ignorees(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "t.csv.gz"
            with gzip.open(f, "wt", encoding="utf-8") as g:
                g.write("ville,heure_utc,T2M,T2MDEW,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_LW_DWN,CLRSKY_SFC_LW_DWN\n")
                g.write("X,2024010100,30,20,0,400,380\n")
                g.write("X,2024010101,-999,20,0,400,380\n")
            self.assertEqual(len(charger(f)["X"]), 1)

    def test_jeu_de_donnees_complet(self):
        villes = charger()
        self.assertEqual(len(villes), 8)
        for nom, hs in villes.items():
            self.assertEqual(len(hs), 8784, nom)  # 2024 est bissextile : 366 × 24 heures


if __name__ == "__main__":
    unittest.main()
