"""Attaques contre les adaptateurs et la garde : montants illisibles, lignes sans preuve, coûts absents
comptés pour zéro, secrets transmis au rejeu, rejeu qui écrit dans un module, fuites dans le public."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

from mere import controles, garde, sources
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
        for faux in ("abc", "1,234", "", "12,5,0", "Infinity", "NaN", "-Infinity"):
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
        contacts = next(x for x in sources.faits_pipeline(evenements, ["o"], "p", 0) if x.opportunite == "o"
                        and x.indicateur == "prospects_contactes")
        self.assertEqual((contacts.valeur, contacts.statut), (2, INCONNU))

    def test_pipeline_absent(self) -> None:
        evenements, _ = sources.lire_pipeline(Path("/nulle/part.csv"))
        self.assertIsNone(evenements)
        self.assertTrue(all(x.statut == INCONNU for x in sources.faits_pipeline(None, ["o"], "p", 0)))

    def test_un_prospect_relance_compte_une_fois(self) -> None:
        ev = [sources.Evenement("2026-11-21", "o", "r1", "envoi", "e", "p"),
              sources.Evenement("2026-11-24", "o", "r1", "relance", "e", "p")]
        x = next(f for f in sources.faits_pipeline(ev, ["o"], "p", 0) if f.opportunite == "o"
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
        self.assertEqual((total.valeur, total.statut), (1200, INCONNU), "une ligne rejetée rend le total INCONNU")


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
        self.assertEqual(sources.normaliser_statut("En préparation : relecture"), "en_preparation")
        self.assertEqual(sources.normaliser_statut("En pause"), "gele")
        self.assertEqual(sources.normaliser_statut("Inactif depuis octobre"), "gele")
        # Régression : « A_REMPLACER » au milieu d'une description n'est pas un statut.
        self.assertEqual(sources.normaliser_statut("Site non mis en ligne, lien (A_REMPLACER)"), "inconnu")


class Rejeu(unittest.TestCase):
    """Les suites sont rejouées par la mère dans un clone neuf : le module ne se valide pas lui-même."""

    def depot(self, d: str, fichiers: dict[str, str] | None = None) -> Path:
        p = Path(d)
        subprocess.run(["git", "init", "-q"], cwd=p, check=True, capture_output=True)
        for nom, texte in (fichiers or {"lisez-moi": "x"}).items():
            (p / nom).write_text(texte, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=p, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "i"], cwd=p,
                       check=True, capture_output=True)
        return p

    def test_issues(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.depot(d)
            ok = controles.rejouer_propre("m", p, ["python3", "-c", "print('3 passed in 0.1s')"], r"^[1-9]\d* passed")
            muet = controles.rejouer_propre("m", p, ["python3", "-c", "print('rien')"], r"^[1-9]\d* passed")
            rouge = controles.rejouer_propre("m", p, ["python3", "-c", "import sys; print('3 passed'); sys.exit(1)"],
                                             r"^[1-9]\d* passed")
        self.assertEqual([r["statut"] for r in (ok, muet, rouge)], [PROUVE, INCONNU, ECHEC])
        self.assertEqual(len(ok["essais"]), 2)

    def test_le_rejeu_tourne_dans_un_clone_et_non_dans_le_depot(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.depot(d)
            r = controles.rejouer_propre("m", p, ["python3", "-c", "open('trace','w'); print('1 passed')"],
                                         r"^[1-9]\d* passed")
            self.assertFalse((p / "trace").exists())
        self.assertEqual(r["statut"], PROUVE)

    def test_un_rejeu_qui_ecrit_dans_le_depot_d_origine_ne_prouve_rien(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.depot(d)
            cmd = ["python3", "-c", f"open({str(p / 'intrus')!r},'w'); print('1 passed')"]
            r = controles.rejouer_propre("m", p, cmd, r"^[1-9]\d* passed")
        self.assertEqual(r["statut"], INCONNU)

    def test_executions_discordantes(self) -> None:
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as compteur:
            p = self.depot(d)
            c = Path(compteur) / "n"
            script = (f"import pathlib,sys; f=pathlib.Path({str(c)!r}); n=int(f.read_text()) if f.exists() else 0; "
                      "f.write_text(str(n+1)); print('2 passed'); sys.exit(n)")
            r = controles.rejouer_propre("m", p, ["python3", "-c", script], r"^[1-9]\d* passed")
        self.assertEqual(r["statut"], "CONFLIT")

    def test_aucun_test_execute_ne_prouve_rien(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.depot(d)
            r = controles.rejouer_propre("m", p, ["python3", "-c", "print('# pass 0')"], r"^# pass \d+")
        self.assertNotEqual(r["statut"], PROUVE)

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

    def test_preuve_perimee_sur_un_autre_commit_ou_un_depot_modifie(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.depot(d)
            r = controles.rejouer_propre("m", p, ["python3", "-c", "print('1 passed')"], r"^[1-9]\d* passed")
            self.assertEqual(controles.controle_suite(r, p).statut, PROUVE)
            (p / "lisez-moi").write_text("modifié", encoding="utf-8")
            self.assertEqual(controles.controle_suite(r, p).statut, INCONNU)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "j"], cwd=p,
                           check=True)
            self.assertEqual(controles.controle_suite(r, p).statut, INCONNU)

    def test_ancien_format_refuse(self) -> None:
        ancien = {"nom": "m", "date": "2026-11-24T00:00:00+00:00", "code": 0, "statut": PROUVE, "bilan": "1 passed",
                  "commit": "abc", "propre": True}
        self.assertEqual(controles.controle_suite(ancien, None).statut, INCONNU)

    def test_depot_absent(self) -> None:
        self.assertEqual(controles.rejouer_propre("m", None, ["true"], "x")["statut"], INCONNU)


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
