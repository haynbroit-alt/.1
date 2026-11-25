"""Tests du modèle : chaque test vérifie une loi physique connue ou une cohérence interne, pas un résultat voulu."""
import math
import unittest

from modele import (SIGMA, Ciel, Surface, bilan, emissivite_berdahl_martin, emissivite_fenetre_cone,
                    exitance_spectrale, fraction_bande, puissance_radiative_nette, temperature_equilibre)


class LoisPhysiques(unittest.TestCase):
    def test_planck_redonne_stefan_boltzmann(self):
        # L'intégrale de Planck sur tout le spectre doit égaler σT⁴ (à 0,5 % près, bornes 0,5–1000 µm).
        for t in (250.0, 300.0, 330.0):
            total = fraction_bande(t, 0.5, 1000.0)
            self.assertAlmostEqual(total, 1.0, delta=0.005, msg=f"T={t}")

    def test_loi_de_wien(self):
        # Le maximum de l'émission spectrale est à λ = 2898 µm·K / T.
        t = 300.0
        lams = [5 + i * 0.01 for i in range(1000)]
        lam_max = max(lams, key=lambda l: exitance_spectrale(l, t))
        self.assertAlmostEqual(lam_max, 2897.77 / t, delta=0.02)

    def test_emissivite_fenetre_bornes(self):
        self.assertAlmostEqual(emissivite_fenetre_cone(0.0), 1.0, places=6)   # opaque
        self.assertAlmostEqual(emissivite_fenetre_cone(1.0), 0.0, places=6)   # transparente
        # Au zénith seul (cône très étroit) : 1 - t0, rapporté au poids du cône sin²θ.
        t0, angle = 0.6, 2.0
        cone = math.sin(math.radians(angle)) ** 2
        self.assertAlmostEqual(emissivite_fenetre_cone(t0, angle) / cone, 1 - t0, delta=1e-3)


class CoherenceDuCiel(unittest.TestCase):
    def test_calage_sur_berdahl_martin(self):
        for rosee in (0, 12, 24):
            ciel = Ciel(300.0, rosee)
            self.assertTrue(ciel.calage_exact)
            fw = ciel.fraction_fenetre
            eps = (1 - fw) + fw * emissivite_fenetre_cone(ciel.t0)
            self.assertAlmostEqual(eps, emissivite_berdahl_martin(rosee), places=6)

    def test_ciel_trop_sec_signale(self):
        # À -10 °C de point de rosée, l'émissivité mesurée (0,662) est sous le minimum du modèle à deux bandes :
        # le modèle doit le dire au lieu de produire un faux calage.
        ciel = Ciel(300.0, -10)
        self.assertFalse(ciel.calage_exact)
        self.assertFalse(ciel.dans_le_domaine_valide)
        self.assertEqual(ciel.t0, 1.0)

    def test_plus_humide_moins_transparent(self):
        t0 = [Ciel(300.0, r).t0 for r in (-10, 0, 10, 20, 24)]
        self.assertEqual(t0, sorted(t0, reverse=True))


class Bilan(unittest.TestCase):
    def test_corps_noir_gris_a_temperature_ambiante(self):
        # Émetteur gris (même ε partout), sans cône, à la température de l'air : P = ε (1 - ε_ciel) σ Ta⁴.
        ciel = Ciel(303.0, 20)
        s = Surface("gris", 0.9, 0.9)
        attendu = 0.9 * (1 - ciel.emissivite_totale) * SIGMA * 303.0 ** 4
        self.assertAlmostEqual(puissance_radiative_nette(s, ciel, 303.0), attendu, delta=0.05)

    def test_cone_complet_egal_sans_ecran(self):
        ciel = Ciel(305.0, 24)
        a = puissance_radiative_nette(Surface("a", demi_angle_deg=90.0), ciel, 300.0)
        b = puissance_radiative_nette(Surface("b"), ciel, 300.0)
        self.assertAlmostEqual(a, b, places=9)

    def test_equilibre_annule_le_bilan(self):
        ciel = Ciel(305.0, 24)
        s = Surface("blanc", absorption_solaire=0.03)
        te = temperature_equilibre(s, ciel, 900.0, 6.0)
        self.assertAlmostEqual(bilan(s, ciel, te, 900.0, 6.0), 0.0, delta=1e-6)

    def test_plus_de_soleil_plus_chaud(self):
        ciel = Ciel(305.0, 20)
        s = Surface("blanc", absorption_solaire=0.05)
        self.assertLess(temperature_equilibre(s, ciel, 0.0, 6.0), temperature_equilibre(s, ciel, 900.0, 6.0))

    def test_moins_de_convection_plus_ecart(self):
        # Hors soleil, une surface sous l'ambiante s'en éloigne davantage si l'air l'échauffe moins.
        ciel = Ciel(300.0, 10)
        s = Surface("blanc", absorption_solaire=0.0)
        self.assertLess(temperature_equilibre(s, ciel, 0.0, 2.0), temperature_equilibre(s, ciel, 0.0, 8.0))


if __name__ == "__main__":
    unittest.main()
