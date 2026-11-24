"""Attaques contre les adaptateurs et la garde : montants illisibles, lignes sans preuve, coûts absents
comptés pour zéro, secrets transmis au rejeu, rejeu qui écrit dans un module, fuites dans le public."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

from mere import garde, sources
from mere.statuts import ECHEC, INCONNU, PROUVE


def ecrire(dossier: Path, nom: str, texte: str) -> Path:
    p = dossier / nom
    p.write_text(texte, encoding="utf-8")
    return p


class Montants(unittest.TestCase):
    def test_lecture(self) -> None:
        self.assertEqual(sources.euros_en_centimes("12,50 €"), 1250)
        self.assertEqual(sources.euros_en_centimes("1 234,56 €"), 123_456)
        self.assertEqual(sources.euros_en_centimes("0 €"), 0)
        for faux in ("abc", "1,234", "", "12,5,0"):
            with self.subTest(faux=faux), self.assertRaises(ValueError):
                sources.euros_en_centimes(faux)


class Pipeline(unittest.TestCase):
    def test_lignes_invalides_rejetees_et_sans_preuve_inconnues(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = ecrire(Path(d), "p.csv", "date;opportunite;ref;etape;canal;preuve\n"
                       "2026-11-21T10:00;o;r1;envoi;email;gmail:1\n"
                       "2026-11-21T10:00;o;r2;envoi;email;\n"
                       "2026-11-21T10:00;o;r3;vendu;email;gmail:3\n"
                       "pas une date;o;r4;envoi;email;gmail:4\n"
                       "2026-11-22;o;;reponse;email;gmail:5\n")
            evenements, erreurs = sources.lire_pipeline(p)
        self.assertEqual(len(evenements or []), 2)
        self.assertEqual(len(erreurs), 3)
        contacts = next(x for x in sources.faits_pipeline(evenements, ["o"], "p") if x.opportunite == "o"
                        and x.indicateur == "prospects_contactes")
        self.assertEqual((contacts.valeur, contacts.statut), (2, INCONNU))

    def test_pipeline_absent(self) -> None:
        evenements, _ = sources.lire_pipeline(Path("/nulle/part.csv"))
        self.assertIsNone(evenements)
        self.assertTrue(all(x.statut == INCONNU for x in sources.faits_pipeline(None, ["o"], "p")))

    def test_un_prospect_relance_compte_une_fois(self) -> None:
        ev = [sources.Evenement("2026-11-21", "o", "r1", "envoi", "e", "p"),
              sources.Evenement("2026-11-24", "o", "r1", "relance", "e", "p")]
        x = next(f for f in sources.faits_pipeline(ev, ["o"], "p") if f.opportunite == "o"
                 and f.indicateur == "prospects_contactes")
        self.assertEqual(x.valeur, 1)


class Couts(unittest.TestCase):
    def test_absence_de_journal_n_est_pas_zero(self) -> None:
        faits, _ = sources.lire_couts(Path("/nulle/part.csv"), "c")
        self.assertTrue(all(f.statut == INCONNU and f.valeur is None for f in faits))

    def test_valeurs_negatives_rejetees(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = ecrire(Path(d), "c.csv", "date;opportunite;euros;heures;preuve\n2026-11-24;o;-10;0;f\n"
                       "2026-11-24;o;12,00;1,5;facture 1\n")
            faits, erreurs = sources.lire_couts(p, "c")
        self.assertEqual(len(erreurs), 1)
        total = next(f for f in faits if f.opportunite == "o" and f.indicateur == "couts")
        self.assertEqual((total.valeur, total.statut), (1200, PROUVE))


class Verdicts(unittest.TestCase):
    def test_verdict_echu_non_rendu(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = ecrire(Path(d), "P.csv", "id;date_verdict;libelle;unite;bas;central;haut;reel;sens\n"
                       "P-1;2026-11-20;x;u;1;2;3;;plus\nP-2;2026-12-20;y;u;1;2;3;;plus\n")
            faits = sources.faits_verdicts(sources.lire_previsions(p), {"P-1": "o", "P-2": "o"},
                                           date(2026, 11, 24), "P")
        rendus = next(f for f in faits if f.opportunite == "o" and f.indicateur == "verdicts_rendus")
        self.assertEqual(rendus.statut, ECHEC)
        self.assertIn("P-1", rendus.note)


class StatutsDeclares(unittest.TestCase):
    def test_lecture_du_premier_mot(self) -> None:
        self.assertEqual(sources.normaliser_statut("Gelé (aucune offre testée)"), "gele")
        self.assertEqual(sources.normaliser_statut("Actif : test commercial"), "actif")
        self.assertEqual(sources.normaliser_statut("Préparé hors ligne ; validation…"), "en_preparation")
        self.assertEqual(sources.normaliser_statut("Remplacé par Obligato"), "arrete")
        self.assertEqual(sources.normaliser_statut("Test en cours (7 envois), verdict le 05/12"), "test")
        # Régression : « A_REMPLACER » au milieu d'une description n'est pas un statut.
        self.assertEqual(sources.normaliser_statut("Site non mis en ligne, lien (A_REMPLACER)"), "inconnu")


class Rejeu(unittest.TestCase):
    def depot(self, d: str) -> Path:
        p = Path(d)
        for cmd in (["git", "init", "-q"], ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                                             "--allow-empty", "-m", "i"]):
            subprocess.run(cmd, cwd=p, check=True, capture_output=True)
        return p

    def test_issues(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.depot(d)
            ok = sources.rejouer("m", p, ["python3", "-c", "print('3 passed')"], r"^\d+ passed")
            muet = sources.rejouer("m", p, ["python3", "-c", "print('rien')"], r"^\d+ passed")
            rouge = sources.rejouer("m", p, ["python3", "-c", "import sys; print('3 passed'); sys.exit(1)"],
                                    r"^\d+ passed")
            ecrit = sources.rejouer("m", p, ["python3", "-c", "open('x','w'); print('3 passed')"], r"^\d+ passed")
        self.assertEqual([r["statut"] for r in (ok, muet, rouge, ecrit)], [PROUVE, INCONNU, ECHEC, INCONNU])
        self.assertIn("modifié", ecrit["note"])

    def test_aucun_secret_transmis(self) -> None:
        os.environ["MERE_TEST_SECRET_KEY"] = "s3cr3t"
        os.environ["GITHUB_TOKEN"] = "ghp_x"
        try:
            env = sources.environnement_propre()
        finally:
            del os.environ["MERE_TEST_SECRET_KEY"], os.environ["GITHUB_TOKEN"]
        self.assertNotIn("MERE_TEST_SECRET_KEY", env)
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertIn("PATH", env)

    def test_preuve_perimee_sur_un_autre_commit(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.depot(d)
            r = sources.rejouer("m", p, ["python3", "-c", "print('1 passed')"], r"^\d+ passed")
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty",
                            "-m", "j"], cwd=p, check=True)
            faits = sources.faits_rejeux([r], {"m": p}, {"m": ["o"]})
        self.assertTrue(all(f.statut == INCONNU for f in faits))

    def test_depot_absent(self) -> None:
        self.assertEqual(sources.rejouer("m", None, ["true"], "x")["statut"], INCONNU)


class Garde(unittest.TestCase):
    def test_fuites_detectees(self) -> None:
        for texte in ("écrire à jean.dupont@exemple.fr", "appeler le 06 12 34 56 78", "SIREN 552 100 554",
                      "paiement ch_3TnOk2Fx9dRNalKW1K", "clé sk_live_abcdef123456", "message 1a20ec6851bd5165",
                      "encaissé : 1 234,00 €"):
            with self.subTest(texte=texte):
                self.assertTrue(garde.fuites(texte))

    def test_texte_propre(self) -> None:
        propre = "26 prospects contactés, 0 réponse, encaissé [privé], 292 passed, commit 7cddfbd53ae6"
        self.assertEqual(garde.fuites(propre), [])

    def test_prix_public_declare_accepte(self) -> None:
        self.assertEqual(garde.fuites("au moins 39 € HT", {"39"}), [])
        self.assertTrue(garde.fuites("au moins 49 € HT", {"39"}))


if __name__ == "__main__":
    unittest.main()
