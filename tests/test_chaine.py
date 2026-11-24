"""Attaques contre la chaîne : déclarations gonflées, registres en retard, verdicts esquivés, hypothèses qui
font monter une opportunité, statuts contredits par l'activité réelle."""

from __future__ import annotations

import unittest
from datetime import date

from mere import chaine
from mere.faits import Fait
from mere.portefeuille import CRITERES, Arret, Note, Opportunite
from mere.sources import Declaration, Evenement, Prevision
from mere.statuts import CONFLIT, ECHEC, INCONNU, PROUVE, combiner


def opp(oid: str = "o", statut: str = "actif", notes: dict[str, tuple[int, str]] | None = None,
        arrets: list[Arret] | None = None, previsions: list[str] | None = None) -> Opportunite:
    o = Opportunite(oid, oid, "m", statut, "r", "a", previsions=previsions or [], arrets=arrets or [])
    for k in CRITERES:
        n, nature = (notes or {}).get(k, (0, "hypothèse"))
        o.notes[k] = Note(k, n, nature, "source" if nature != "hypothèse" else "", "")
    return o


def f(ind: str, valeur, statut: str = PROUVE, module: str = "x", o: str = "o", prive: bool = False) -> Fait:
    return Fait(module, ind, valeur, statut, "test", o, "2026-11-24", "preuve" if statut == PROUVE else "",
                prive=prive)


class Statuts(unittest.TestCase):
    def test_combinaison(self) -> None:
        self.assertEqual(combiner([]), INCONNU)
        self.assertEqual(combiner([PROUVE, PROUVE]), PROUVE)
        self.assertEqual(combiner([PROUVE, INCONNU]), INCONNU)
        self.assertEqual(combiner([PROUVE, ECHEC, INCONNU]), ECHEC)
        self.assertEqual(combiner([ECHEC, CONFLIT]), CONFLIT)
        with self.assertRaises(ValueError):
            combiner(["VALIDÉ"])

    def test_un_fait_prouve_exige_une_preuve(self) -> None:
        with self.assertRaises(ValueError):
            Fait("x", "ventes_payees", 3, PROUVE, "déclaration orale")
        with self.assertRaises(ValueError):
            Fait("x", "ventes_payees", None, PROUVE, "s", preuve="p")

    def test_montants_entiers_et_prives(self) -> None:
        with self.assertRaises(ValueError):
            Fait("x", "encaisse_net", 12.5, PROUVE, "s", preuve="p", prive=True)
        with self.assertRaises(ValueError):
            Fait("x", "encaisse_net", 1250, PROUVE, "s", preuve="p", prive=False)
        with self.assertRaises(ValueError):
            Fait("x", "potentiel_estime", 10, INCONNU, "s")


class Consolidation(unittest.TestCase):
    def test_deux_sources_prouvees_qui_divergent(self) -> None:
        c = chaine.consolider([f("reponses", 2, module="a"), f("reponses", 3, module="b")])
        self.assertEqual(chaine.lire(c, "o", "reponses").statut, CONFLIT)

    def test_un_conflit_contamine(self) -> None:
        c = chaine.consolider([f("reponses", 2), f("reponses", 2, statut=CONFLIT, module="controle")])
        self.assertEqual(chaine.lire(c, "o", "reponses").statut, CONFLIT)

    def test_absent_est_inconnu(self) -> None:
        self.assertEqual(chaine.lire({}, "o", "ventes_payees").statut, INCONNU)


class Rapprochement(unittest.TestCase):
    encaissements = [("2026-11-20T10:00:00+00:00", 2_900, "o")]

    def test_encaisse_declare_gonfle(self) -> None:
        faits, _ = chaine.rapprocher([Declaration("portail", "encaisse_net", 50_000, "2026-11-24", "s")],
                                     self.encaissements, [], {})
        self.assertEqual([x.statut for x in faits], [CONFLIT])

    def test_encaisse_declare_avant_le_paiement_concorde(self) -> None:
        faits, _ = chaine.rapprocher([Declaration("portail", "encaisse_net", 0, "2026-11-19", "s")],
                                     self.encaissements, [], {})
        self.assertEqual(faits, [])

    def test_encaisse_declare_nul_apres_un_paiement(self) -> None:
        faits, _ = chaine.rapprocher([Declaration("portail", "encaisse_net", 0, "2026-11-21", "s")],
                                     self.encaissements, [], {})
        self.assertEqual([x.statut for x in faits], [CONFLIT])

    def test_encaisse_declare_sans_prestataire_lisible(self) -> None:
        faits, alertes = chaine.rapprocher([Declaration("portail", "encaisse_net", 0, "2026-11-21", "s")],
                                           None, [], {})
        self.assertEqual(faits, [])
        self.assertTrue(alertes)

    def envois(self, heure: str) -> list[Evenement]:
        return [Evenement(f"2026-11-21{heure}", "o", f"r{i}", "envoi", "email", "p") for i in range(3)]

    def test_registre_en_retard_n_est_pas_un_conflit(self) -> None:
        d = Declaration("velyx", "prospects_contactes", 0, "2026-11-21T08:22:52", "s")
        faits, alertes = chaine.rapprocher([d], [], self.envois("T11:03"), {"o": "velyx"})
        self.assertEqual(faits, [])
        self.assertIn("en retard", alertes[0])

    def test_registre_qui_ignore_ses_propres_envois(self) -> None:
        d = Declaration("velyx", "prospects_contactes", 0, "2026-11-21T08:22:52", "s")
        faits, _ = chaine.rapprocher([d], [], self.envois("T07:00"), {"o": "velyx"})
        self.assertEqual([x.statut for x in faits], [CONFLIT])

    def test_meme_jour_sans_heure_reste_indecidable(self) -> None:
        d = Declaration("velyx", "prospects_contactes", 0, "2026-11-21T08:22:52", "s")
        faits, alertes = chaine.rapprocher([d], [], self.envois(""), {"o": "velyx"})
        self.assertEqual((faits, alertes), ([], []))


class CriteresDArret(unittest.TestCase):
    jour = date(2026, 11, 24)

    def etat(self, valeur, statut: str = PROUVE, quand: str = "2026-11-30") -> chaine.EtatArret:
        o = opp(arrets=[Arret("l", "reponses", 1, "min", quand, "")])
        faits = [] if valeur is None else [f("reponses", valeur, statut=statut)]
        return chaine.evaluer_arrets(o, chaine.consolider(faits), self.jour, [])[0]

    def test_avant_la_date(self) -> None:
        e = self.etat(0)
        self.assertEqual((e.statut, e.detail), (INCONNU, "en attente, J-6"))

    def test_atteint_avant_la_date(self) -> None:
        self.assertEqual(self.etat(2).statut, PROUVE)

    def test_manque_a_la_date(self) -> None:
        self.assertEqual(self.etat(0, quand="2026-11-24").statut, ECHEC)

    def test_echu_sans_mesure(self) -> None:
        e = self.etat(None, quand="2026-11-20")
        self.assertEqual((e.statut, e.detail), (INCONNU, "verdict dû sans mesure"))

    def test_mesure_en_conflit(self) -> None:
        self.assertEqual(self.etat(1, statut=CONFLIT).statut, CONFLIT)

    def test_prevision_echue_sans_resultat(self) -> None:
        o = opp(previsions=["P-1"])
        p = Prevision("P-1", "2026-11-20", "l", 1, 2, None, "plus")
        e = chaine.evaluer_arrets(o, {}, self.jour, [p])[0]
        self.assertEqual(e.statut, ECHEC)

    def test_prevision_sous_la_fourchette_basse(self) -> None:
        o = opp(previsions=["P-1"])
        e = chaine.evaluer_arrets(o, {}, self.jour, [Prevision("P-1", "2026-11-20", "l", 3, 8, 1, "plus")])[0]
        self.assertEqual(e.statut, ECHEC)


class Chaine(unittest.TestCase):
    def test_demande_supposee_n_est_pas_prouvee(self) -> None:
        o = opp(notes={"demande": (5, "hypothèse")})
        self.assertEqual(chaine.etats_chaine(o, {}, [])["opportunite"][0], INCONNU)

    def test_critere_manque_marque_l_etape(self) -> None:
        o = opp(arrets=[Arret("l", "reponses", 1, "min", "2026-11-20", "")])
        c = chaine.consolider([f("reponses", 0), f("prospects_qualifies", 0)])
        arrets = chaine.evaluer_arrets(o, c, date(2026, 11, 24), [])
        self.assertEqual(chaine.etats_chaine(o, c, arrets)["acheteur"][0], ECHEC)

    def test_argent_encaisse_franchit_l_etape(self) -> None:
        o = opp()
        c = chaine.consolider([f("encaisse_net", 3_900, prive=True), f("ventes_payees", 1)])
        e = chaine.etats_chaine(o, c, [])
        self.assertEqual((e["vente"][0], e["encaisse"][0]), (PROUVE, PROUVE))

    def test_les_hypotheses_ne_departagent_pas(self) -> None:
        reve = opp("reve", notes={k: (5, "hypothèse") for k in CRITERES})
        reel = opp("reel", notes={"demande": (2, "mesuré")})
        lignes = [(o, chaine.etats_chaine(o, {}, [])) for o in (reve, reel)]
        self.assertEqual([o.id for o in chaine.priorites(lignes)], ["reel", "reve"])
        self.assertEqual(reve.score_prouve, 0)

    def test_un_test_passe_apres_les_actifs(self) -> None:
        test = opp("test", statut="test", notes={"demande": (5, "mesuré")})
        actif = opp("actif")
        lignes = [(o, chaine.etats_chaine(o, {}, [])) for o in (test, actif)]
        self.assertEqual([o.id for o in chaine.priorites(lignes)], ["actif", "test"])

    def test_gele_exclu_des_priorites(self) -> None:
        o = opp("g", statut="gele")
        self.assertEqual(chaine.priorites([(o, chaine.etats_chaine(o, {}, []))]), [])

    def test_statut_declare_contredit_par_l_activite(self) -> None:
        o = opp()
        o.declare = {"fichier": "PROJETS.md"}
        self.assertIsNotNone(chaine.conflits_de_statut(o, "gele", 7))
        self.assertIsNotNone(chaine.conflits_de_statut(o, "en_preparation", 1))
        self.assertIsNone(chaine.conflits_de_statut(o, "actif", 7))
        self.assertIsNone(chaine.conflits_de_statut(o, "gele", 0))


if __name__ == "__main__":
    unittest.main()
