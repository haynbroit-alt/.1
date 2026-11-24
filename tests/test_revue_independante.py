"""Non-régression des 19 défauts trouvés par la revue indépendante du 24/11/2026 (journal/C-0002.md), et
tests des contrôles indépendants. Chaque test porte le numéro du défaut qu'il empêche de revenir."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from aides import FauxStripe, paiement

from mere import chaine, controles, garde, portefeuille, sources, stripe
from mere.portefeuille import Arret
from mere.sources import Declaration, Evenement, Prevision
from mere.statuts import CONFLIT, ECHEC, INCONNU, PROUVE

OPPS = {"a": ["Produit A"], "b": ["Produit B"]}


def versionner(dossier: str | Path) -> Path:
    """Commit de tout le contenu d'un dossier : une donnée citée doit être versionnée pour être opposable."""
    import subprocess
    d = Path(dossier)
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "données"], cwd=d, check=True)
    return d


def fait(r: stripe.Releve, opp: str, ind: str):
    return next((x.valeur, x.statut) for x in r.faits if x.opportunite == opp and x.indicateur == ind)


def releve(charges, correspondances=None, **autres) -> stripe.Releve:
    return stripe.releve(FauxStripe({"charges": charges, **autres}).client(), correspondances or OPPS,
                         opportunites=list(correspondances or OPPS))


class ArgentNonEncaisse(unittest.TestCase):
    def test_f01a_autorisation_non_capturee(self) -> None:
        r = releve([paiement("ch_auth0001", 50_000, captured=False, metadata={"opportunite": "a"})])
        self.assertEqual(fait(r, "a", "encaisse_net"), (0, PROUVE))
        self.assertEqual(fait(r, "a", "ventes_payees"), (0, PROUVE))

    def test_f01b_paiement_conteste(self) -> None:
        r = releve([paiement("ch_disp0001", 30_000, disputed=True, metadata={"opportunite": "b"})])
        self.assertEqual(fait(r, "b", "encaisse_net"), (None, INCONNU))
        self.assertEqual(fait(r, "b", "ventes_payees"), (None, INCONNU))
        perdu = releve([paiement("ch_disp0002", 30_000, disputed=True, metadata={"opportunite": "b"})],
                       disputes=[{"id": "dp_00000001", "charge": "ch_disp0002", "status": "lost", "amount": 30_000}])
        self.assertEqual(fait(perdu, "b", "encaisse_net"), (0, PROUVE))

    def test_f02_attribution_ambigue(self) -> None:
        r = releve([paiement("ch_pro00001", 9900, description="Pack Pro annuel")], {"a": ["Pack"], "b": ["Pack Pro"]})
        self.assertEqual(fait(r, "a", "ventes_payees"), (None, INCONNU))
        self.assertEqual(fait(r, stripe.NON_ATTRIBUE, "ventes_payees"), (1, PROUVE))

    def test_f07_paiement_non_attribue_rend_tout_inconnu(self) -> None:
        r = releve([paiement("ch_fail0001", 4900, statut="failed", metadata={"opportunite": "a"}),
                    paiement("ch_orph0001", 4900, description="divers")])
        self.assertEqual(fait(r, "a", "encaisse_net"), (None, INCONNU))
        self.assertEqual(fait(r, "b", "encaisse_net"), (None, INCONNU))

    def test_f08_offre_sans_prix_reel(self) -> None:
        produit = {"id": "prod_T0000001", "name": "Produit A", "active": True, "livemode": False}
        r = releve([], products=[produit], prices=[])
        self.assertEqual(fait(r, "a", "offres_actives"), (0, PROUVE))
        reel = {**produit, "livemode": True}
        r = releve([], products=[reel], prices=[{"id": "price_T00001", "product": "prod_T0000001", "active": True,
                                                  "livemode": True}])
        self.assertEqual(fait(r, "a", "offres_actives"), (1, PROUVE))

    def test_f19_devise_en_majuscules(self) -> None:
        r = stripe.releve(FauxStripe({"charges": [paiement("ch_eur00001", 4900, metadata={"opportunite": "a"})]})
                          .client(), OPPS, devise="EUR", opportunites=["a"])
        self.assertEqual(fait(r, "*", "encaisse_net"), (4900, PROUVE))


class Sources(unittest.TestCase):
    def ecrire(self, d: str, nom: str, texte: str) -> Path:
        p = Path(d) / nom
        p.write_text(texte, encoding="utf-8")
        return p

    def test_f03_ligne_de_cout_illisible(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.ecrire(d, "c.csv", "date;opportunite;euros;heures;preuve\n2026-11-24;o;120 EUR;0;f\n"
                            "2026-11-24;o;10,00;0;f\n")
            faits, erreurs = sources.lire_couts(p, "c")
        total = next(f for f in faits if f.opportunite == "o" and f.indicateur == "couts")
        self.assertEqual(total.statut, INCONNU)
        self.assertNotIn("120 EUR", " ".join(erreurs), "f04 : le contenu d'une cellule n'est jamais recopié")

    def test_f04_contenu_de_cellule_jamais_recopie(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.ecrire(d, "p.csv", "date;opportunite;ref;etape;preuve\n"
                            "2026-11-21;o;r1;Boulangerie Martin Lyon;g\n")
            _, erreurs = sources.lire_pipeline(p)
        self.assertTrue(erreurs)
        self.assertNotIn("Boulangerie", " ".join(erreurs))

    def test_f09_lignes_rejetees_ou_bom(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = self.ecrire(d, "p.csv", "﻿date;opportunite;ref;etape;preuve\n2026-11-21;o;r1;envoi;g\n"
                            "21/11/2026;o;r1;reponse;g\n")
            ev, erreurs = sources.lire_pipeline(p)
        self.assertEqual(len(ev or []), 1, "l'en-tête avec BOM est lu")
        rep = next(f for f in sources.faits_pipeline(ev, ["o"], "p", len(erreurs))
                   if f.opportunite == "o" and f.indicateur == "reponses")
        self.assertEqual(rep.statut, INCONNU, "une ligne rejetée interdit de prouver le compte")

    def test_f10_perdu_n_est_pas_une_reponse(self) -> None:
        ev = [Evenement("2026-11-21", "o", "r1", "envoi", "e", "p"),
              Evenement("2026-11-30", "o", "r1", "perdu", "e", "p")]
        rep = next(f for f in sources.faits_pipeline(ev, ["o"], "p", 0) if f.opportunite == "o"
                   and f.indicateur == "reponses")
        self.assertEqual(rep.valeur, 0)

    def test_f15_libelles_de_statut(self) -> None:
        o = portefeuille.Opportunite("o", "o", "m", "actif", "r", "a", declare={"fichier": "P.md"})
        for libelle in ("En préparation : relecture", "En pause", "Inactif"):
            with self.subTest(libelle=libelle):
                self.assertIsNotNone(chaine.conflits_de_statut(o, sources.normaliser_statut(libelle), 3))

    def test_f17_entrees_malformees_sans_plantage(self) -> None:
        for faux in ("Infinity", "1e3", "0x10"):
            with self.assertRaises(ValueError):
                sources.euros_en_centimes(faux)
        with tempfile.TemporaryDirectory() as d:
            p = self.ecrire(d, "P.csv", "id;date_verdict;libelle;unite;bas;central;haut;reel;sens\n"
                            "P-1;22/11/2026;x;u;1;2;3;;plus\nP-2;2026-11-22;y;u;1;2;3;n/a;plus\n"
                            "P-3;2026-11-22;z;u;1;2;3;;plus\n")
            erreurs: list[str] = []
            prev = sources.lire_previsions(p, erreurs)
        self.assertEqual([x.id for x in prev or []], ["P-3"])
        self.assertEqual(len(erreurs), 2)


class Chaine(unittest.TestCase):
    def test_f11_un_resultat_tardif_ne_rattrape_pas_une_date_manquee(self) -> None:
        o = portefeuille.Opportunite("o", "o", "m", "actif", "r", "a",
                                     arrets=[Arret("une réponse", "reponses", 1, "min", "2026-11-20", "")])
        c = chaine.consolider([sources.Fait("pipeline", "reponses", 1, PROUVE, "p", "o", "2026-11-23", "p")])
        def a_la_date(opp: str, ind: str, limite: date) -> tuple[int, str]:
            return 0, PROUVE  # aucune réponse au 20/11
        e = chaine.evaluer_arrets(o, c, date(2026, 11, 24), [], a_la_date)[0]
        self.assertEqual(e.statut, ECHEC)

    def test_f11_un_plafond_ne_se_valide_pas_avant_sa_date(self) -> None:
        o = portefeuille.Opportunite("o", "o", "m", "actif", "r", "a",
                                     arrets=[Arret("coûts plafonnés", "heures", 50, "max", "2026-12-31", "")])
        c = chaine.consolider([sources.Fait("couts", "heures", 10, PROUVE, "c", "o", "", "p")])
        self.assertEqual(chaine.evaluer_arrets(o, c, date(2026, 11, 24), [])[0].statut, INCONNU)

    def test_f12_sens_des_previsions(self) -> None:
        o = portefeuille.Opportunite("o", "o", "m", "actif", "r", "a", previsions=["G"])
        mauvais = Prevision("G", "2026-11-20", "coût", 100, 120, 900, "moins", 150)
        bon = Prevision("G", "2026-11-20", "coût", 100, 120, 50, "moins", 150)
        self.assertEqual(chaine.evaluer_arrets(o, {}, date(2026, 11, 24), [mauvais])[0].statut, ECHEC)
        self.assertEqual(chaine.evaluer_arrets(o, {}, date(2026, 11, 24), [bon])[0].statut, PROUVE)

    def test_f13_declaration_comparee_a_son_perimetre(self) -> None:
        enc = [("2026-11-20T10:00:00+00:00", 3900, "x")]
        d = Declaration("velyx", "encaisse_net", 3900, "2026-11-24T00:00:00Z", "s", perimetre="velyx")
        faits, _ = chaine.rapprocher([d], enc, [], {"x": "autre", "v": "velyx"})
        self.assertEqual([f.statut for f in faits], [CONFLIT], "l'argent d'un autre module n'est pas le sien")
        d0 = Declaration("velyx", "encaisse_net", 0, "2026-11-24T00:00:00Z", "s", perimetre="velyx")
        self.assertEqual(chaine.rapprocher([d0], enc, [], {"x": "autre", "v": "velyx"})[0], [])

    def test_f14_dates_avec_fuseaux_et_espaces(self) -> None:
        d = Declaration("velyx", "prospects_contactes", 0, "2026-11-21T08:22:52Z", "s")
        avant = [Evenement("2026-11-21T09:00+01:00", "o", "r1", "envoi", "e", "p")]
        self.assertEqual([f.statut for f in chaine.rapprocher([d], [], avant, {"o": "velyx"})[0]], [CONFLIT])
        apres = [Evenement("2026-11-21 23:00", "o", "r1", "envoi", "e", "p")]
        faits, alertes = chaine.rapprocher([d], [], apres, {"o": "velyx"})
        self.assertEqual(faits, [])
        self.assertTrue(alertes)

    def test_f18_indicateur_d_arret_inconnu_refuse(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.toml"
            crit = "".join(f'{k} = {{ note = 0, nature = "hypothèse" }}\n' for k in portefeuille.CRITERES)
            p.write_text('[[opportunite]]\nid = "o"\nmodule = "m"\nstatut = "actif"\n[opportunite.criteres]\n' + crit +
                         '[[opportunite.arret]]\nlibelle = "x"\nindicateur = "vente_payees"\nseuil = 1\n'
                         'date = "2026-11-20"\n', encoding="utf-8")
            _, _, erreurs = portefeuille.charger(p)
        self.assertTrue(any("vente_payees" in e for e in erreurs))


class Garde(unittest.TestCase):
    def test_f05_motifs_manques(self) -> None:
        for texte in ("SIREN 552100554.", "SIRET 55210055400025,", "FR12552100554", "+33-6-12-34-56-78",
                      "0033 6 12 34 56 78", "pi_3Tabc_secret_abcdef123", "cs_live_a1b2c3d4e5f6", "pm_1AbCdEfGhIj",
                      "dp_1AbCdEfGhIj", "whsec_abcdef123456", "sk-ant-api03-abcdefghijkl", "1 200 EUR", "12 k€",
                      "€1234"):
            with self.subTest(texte=texte):
                self.assertTrue(garde.fuites(texte))

    def test_f05_pas_de_faux_positif_sur_le_tableau(self) -> None:
        for texte in ("taux_opposition_btp relu", "292 passed in 8.10s", "commit 7cddfbd53ae6",
                      "2026-11-24T19:40:00+00:00", "0,796", "prospects_contactes", "empreinte 229cff3558f3"):
            with self.subTest(texte=texte):
                self.assertEqual(garde.fuites(texte), [])


class ControlesIndependants(unittest.TestCase):
    def test_un_producteur_ne_se_controle_pas_lui_meme(self) -> None:
        for producteur, controleur in (("mere", "mere"), ("rejeu:sovereign", "sovereign"), ("stripe", "stripe:x")):
            with self.subTest(p=producteur, c=controleur), self.assertRaises(controles.AutoValidation):
                controles.Controle("x", "o", producteur, controleur, "m", PROUVE, "d", "2026-11-24")

    def test_citation_page_publique(self) -> None:
        verif = {"url": "https://entreprendre.service-public.gouv.fr/p", "contient": "Affichages obligatoires"}
        page = lambda url: (200, "<html><h1>Affichages&nbsp;obligatoires</h1></html>")  # noqa: E731
        self.assertEqual(controles.controler_citation("o", "demande", verif, {}, page).statut, PROUVE)
        absente = lambda url: (200, "<html>autre chose</html>")  # noqa: E731
        self.assertEqual(controles.controler_citation("o", "demande", verif, {}, absente).statut, ECHEC)
        refus = lambda url: (403, "")  # noqa: E731
        self.assertEqual(controles.controler_citation("o", "demande", verif, {}, refus).statut, INCONNU)

        def panne(url: str) -> tuple[int, str]:
            raise OSError("réseau")
        self.assertEqual(controles.controler_citation("o", "demande", verif, {}, panne).statut, INCONNU)

    def test_citation_donnees_brutes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s.json").write_text(json.dumps({"gardes": 59}), encoding="utf-8")
            (Path(d) / "etude.md").write_text("8 sociétés", encoding="utf-8")
            depots = {"x": versionner(d)}
            faux = controles.controler_citation("o", "potentiel", {"depot": "x", "fichier": "s.json", "cle": "gardes",
                                                                   "valeur": 8}, depots)
            vrai = controles.controler_citation("o", "potentiel", {"depot": "x", "fichier": "s.json", "cle": "gardes",
                                                                   "valeur": 59}, depots)
            prose = controles.controler_citation("o", "potentiel", {"depot": "x", "fichier": "etude.md", "cle": "x"},
                                                 depots)
        # Des données internes peuvent contredire une note (CONFLIT), jamais la prouver seules (A2).
        self.assertEqual((faux.statut, vrai.statut, prose.statut), (CONFLIT, INCONNU, ECHEC))
        self.assertEqual(controles.controler_citation("o", "demande", {}, {}).statut, INCONNU)

    def test_prospects(self) -> None:
        p = controles.Prospect("o", "r1", "exemple.invalid", False)
        vus = {"exemple.invalid"}
        self.assertEqual(controles.controler_prospect(p, lambda u: (200, ""), vus, opposable=True).statut, PROUVE)
        self.assertEqual(controles.controler_prospect(p, lambda u: (200, ""), vus).statut, INCONNU,
                         "relevé de la messagerie fourni hors de la mère : non opposable")
        self.assertEqual(controles.controler_prospect(p, lambda u: (200, "")).statut, INCONNU,
                         "sans second relevé, le domaine écrit par l'auteur n'est pas confirmé")

        def panne(url: str) -> tuple[int, str]:
            raise OSError("réseau")
        self.assertEqual(controles.controler_prospect(p, panne).statut, INCONNU)
        rebond = controles.Prospect("o", "r1", "exemple.invalid", True)
        self.assertEqual(controles.controler_prospect(rebond, lambda u: (200, "")).statut, ECHEC)
        self.assertEqual(controles.controler_prospect(controles.Prospect("o", "r", "", False)).statut, INCONNU)

    def test_banque(self) -> None:
        virement = {"status": "paid", "livemode": True, "amount": 3800, "arrival_date": 1_795_500_000}
        self.assertEqual(controles.rapprocher_virements([], None, date(2026, 11, 24)).statut, PROUVE)
        self.assertEqual(controles.rapprocher_virements([virement], None, date(2026, 11, 24)).statut, INCONNU)
        ok = controles.rapprocher_virements([virement], [("2026-11-25", 3800, "VIR")], date(2026, 11, 26))
        manque = controles.rapprocher_virements([virement], [("2026-11-25", 3700, "VIR")], date(2026, 11, 26))
        self.assertEqual((ok.statut, manque.statut), (PROUVE, CONFLIT))

    def test_controle_par_novarys(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "preuves.jsonl"
            preuve = {"claim": "mere-suite", "status": "PROUVE", "seq": 40, "at": "2026-11-24T20:00:00+00:00",
                      "capability": "c", "subject": {"commit": "abcdef1234567890", "dirty": False, "name": "mere"}}
            p.write_text(json.dumps(preuve) + "\n", encoding="utf-8")
            meme = controles.controle_par_novarys(p, "mere-", "abcdef1234567890")
            autre = controles.controle_par_novarys(p, "mere-", "0000000000000000")
        self.assertEqual((meme[0].statut, autre[0].statut), (PROUVE, INCONNU))
        self.assertEqual(controles.controle_par_novarys(None, "mere-", "x")[0].statut, INCONNU)

    def test_preuve_valable_tant_que_le_code_prouve_ne_change_pas(self) -> None:
        import subprocess

        def git(d: Path, *a: str) -> str:
            return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=d, check=True,
                                  capture_output=True, text=True).stdout.strip()
        with tempfile.TemporaryDirectory() as d:
            racine = Path(d)
            git(racine, "init", "-q")
            (racine / "mere").mkdir()
            (racine / "mere/code.py").write_text("x = 1\n", encoding="utf-8")
            git(racine, "add", "-A")
            git(racine, "commit", "-qm", "a")
            prouve = git(racine, "rev-parse", "HEAD")
            p = racine / "preuves.jsonl"
            p.write_text(json.dumps({"claim": "mere-suite", "status": "PROUVE", "seq": 1, "at": "2026-11-24",
                                     "subject": {"commit": prouve, "dirty": False}}) + "\n", encoding="utf-8")
            (racine / "TABLEAU.md").write_text("régénéré\n", encoding="utf-8")
            git(racine, "add", "-A")
            git(racine, "commit", "-qm", "b")
            tableau_seul = controles.controle_par_novarys(p, "mere-", git(racine, "rev-parse", "HEAD"), racine)
            (racine / "mere/code.py").write_text("x = 2\n", encoding="utf-8")
            code_modifie = controles.controle_par_novarys(p, "mere-", git(racine, "rev-parse", "HEAD"), racine)
        self.assertEqual(tableau_seul[0].statut, PROUVE)
        self.assertEqual(code_modifie[0].statut, INCONNU)


if __name__ == "__main__":
    unittest.main()


class SecondeRevue(unittest.TestCase):
    """Non-régression des 10 défauts trouvés par la seconde revue indépendante (N1 à N10)."""

    def test_n01_qualification_cloisonnee_par_opportunite(self) -> None:
        import tempfile as tf

        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tf.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            # r1 est seulement contacté pour a ; un r1 homonyme est qualifié (avec preuve) pour une autre offre b ;
            # r2 de a est « qualifié » sans preuve.
            with (racine / "prive/pipeline.csv").open("a", encoding="utf-8") as f:
                f.write("2026-11-23T10:00;b;r1;envoi;email;gmail:7\n2026-11-23T11:00;b;r1;qualifie;email;gmail:8\n"
                        "2026-11-23T12:00;a;r2;qualifie;email;\n")
            (racine / "prive/controles_prospects.json").write_text(json.dumps([
                controles.Controle(f"prospect:{o}:{ref}", "o", "pipeline", "web-public", "m", PROUVE, "ok",
                                   "2099-01-01T00:00:00+00:00", opportunite=o).to_dict()
                for o, ref in (("a", "r1"), ("a", "r2"), ("b", "r1"))]), encoding="utf-8")
            r = construire(racine, date(2026, 11, 24))
        self.assertEqual(chaine.lire(r.consolide, "a", "qualifies_verifies").valeur, 0)
        self.assertNotEqual(r.etats["a"]["acheteur"][0], PROUVE)

    def test_n02_un_4xx_ou_une_messagerie_ne_prouvent_rien(self) -> None:
        p = controles.Prospect("o", "r1", "exemple.invalid", False)
        for code in (403, 404, 410):
            self.assertEqual(controles.controler_prospect(p, lambda u, c=code: (c, ""), {"exemple.invalid"}).statut,
                             INCONNU)
        webmail = controles.Prospect("o", "r1", "gmail.com", False)
        self.assertEqual(controles.controler_prospect(webmail, lambda u: (200, "")).statut, INCONNU)
        absent = controles.controler_prospect(p, lambda u: (200, ""), domaines_messagerie={"autre.fr"})
        self.assertEqual(absent.statut, ECHEC, "domaine du pipeline absent du second relevé")

    def test_n03_citation_satisfaite_par_son_propre_auteur(self) -> None:
        page = lambda url: (200, "<p>a b c</p>")  # noqa: E731
        courte = controles.controler_citation("o", "d", {"url": "https://exemple.invalid/", "contient": "a"}, {}, page)
        brute = controles.controler_citation("o", "d", {"url": "https://raw.githubusercontent.com/x/y/main/note.md",
                                                        "contient": "marché très porteur"}, {}, page)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s.json").write_text('{"x": 1}', encoding="utf-8")
            sans_attendu = controles.controler_citation("o", "d", {"depot": "x", "fichier": "s.json", "cle": "x"},
                                                        {"x": Path(d)})
            le_sien = controles.controler_citation("o", "d", {"depot": "mere", "fichier": "s.json", "cle": "x",
                                                              "valeur": 1}, {"mere": Path(d)})
        self.assertEqual([c.statut for c in (courte, brute, sans_attendu, le_sien)], [ECHEC] * 4)

    def test_n04_valeur_citee_non_numerique_jamais_recopiee(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s.json").write_text('{"x": {"client": "Boulangerie Martin"}}', encoding="utf-8")
            c = controles.controler_citation("o", "d", {"depot": "x", "fichier": "s.json", "cle": "x", "valeur": 1},
                                             {"x": versionner(d)})
        self.assertEqual(c.statut, ECHEC)
        self.assertNotIn("Boulangerie", c.detail)

    def test_n05_prevision_illisible_n_efface_pas_le_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "P.csv"
            p.write_text("id;date_verdict;libelle;unite;bas;central;haut;reel;sens\nP-1;2026-11-20;x;u;1;2;3;2;plus\n"
                         "P-2;22/11/2026;y;u;1;2;3;;plus\n", encoding="utf-8")
            rejetees: list[str] = []
            prev = sources.lire_previsions(p, [], rejetees)
        faits = sources.faits_verdicts(prev, {"P-1": "a", "P-2": "a"}, date(2026, 11, 24), "P", rejetees)
        rendus = next(f for f in faits if f.opportunite == "a" and f.indicateur == "verdicts_rendus")
        self.assertEqual(rendus.statut, INCONNU)

    def test_n06_un_compte_croissant_sous_le_seuil_echoue_a_la_date(self) -> None:
        o = portefeuille.Opportunite("o", "o", "m", "actif", "r", "a",
                                     arrets=[Arret("prospects contactés", "prospects_contactes", 5, "min", "2026-11-20",
                                                   "")])
        c = chaine.consolider([sources.Fait("pipeline", "prospects_contactes", 2, PROUVE, "w", "o", "", "p")])
        self.assertEqual(chaine.evaluer_arrets(o, c, date(2026, 11, 24), [])[0].statut, ECHEC)

    def test_n07_tous_les_tests_sautes_ne_prouvent_rien(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q"], cwd=d, check=True)
            (Path(d) / "x").write_text("x", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=d, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i"], cwd=d,
                           check=True)
            r = controles.rejouer_propre("m", Path(d), ["python3", "-c", "print('Ran 2 tests in 0.0s'); "
                                                        "print('OK (skipped=2)')"], r"^OK( |$)")
            hors_git = controles.rejouer_propre("m", Path(d) / "absent", ["true"], "x")
            outil = controles.rejouer_propre("m", Path(d), ["outil-qui-n-existe-pas"], "x")
        self.assertNotEqual(r["statut"], PROUVE)
        self.assertEqual((hors_git["statut"], outil["statut"]), (INCONNU, INCONNU),
                         "N9 : l'environnement est en cause, pas la suite")

    def test_n08_releve_bancaire_windows(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "banque.csv"
            p.write_bytes("date;libelle;montant\n2026-11-25;VIREMENT REÇU;38,00\n".encode("cp1252"))
            lignes, erreurs = controles.lire_releve_bancaire(p)
        self.assertEqual((lignes, erreurs), ([("2026-11-25", 3800, "VIREMENT REÇU")], []))

    def test_n09_second_releve_par_le_pipeline_lui_meme(self) -> None:
        import tempfile as tf

        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tf.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            (racine / "prive/recomptage_messagerie.json").write_text('{"lecteur": "pipeline", "envois": {"a": 2}}',
                                                                     encoding="utf-8")
            r = construire(racine, date(2026, 11, 24))
        self.assertEqual(next(c for c in r.controles if c.id == "pipeline:recomptage").statut, ECHEC)

    def test_n10_garde_et_statuts(self) -> None:
        for texte in ("552.100.554", "552-100-554", "EUR 1 200", "1,2 M€", "**1 200** €", "(+33) 6 12 34 56 78",
                      "06/12/34/56/78", "AKIAIOSFODNN7EXAMPLE", "https://billing.stripe.com/p/session/live_YWNjdF8xVFNXeXZGeDlkUk5h"):
            with self.subTest(texte=texte):
                self.assertTrue(garde.fuites(texte))
        attendus = {"Pas encore actif": "en_preparation", "En veille": "gele", "Stoppé": "arrete",
                    "Archivé": "arrete", "Désactivé": "gele"}
        self.assertEqual({k: sources.normaliser_statut(k) for k in attendus}, attendus)


class TroisiemeRevue(unittest.TestCase):
    """Non-régression des 7 défauts trouvés par la troisième revue indépendante (T1 à T7)."""

    page = staticmethod(lambda url: (200, "<p>Affichages ou diffusions obligatoires</p>"))

    def test_t1_le_producteur_ne_peut_pas_heberger_sa_propre_preuve(self) -> None:
        verif = {"contient": "Affichages ou diffusions obligatoires"}
        for url in ("https://cdn.jsdelivr.net/gh/x/y/PROJETS.md", "https://novarys.onrender.com/p",
                    "https://moi.netlify.app/", "https://sites.google.com/view/x", "https://exemple-inconnu.fr/"):
            with self.subTest(url=url):
                c = controles.controler_citation("o", "d", {**verif, "url": url}, {}, self.page)
                self.assertEqual(c.statut, ECHEC)
        autorite = controles.controler_citation("o", "d", {**verif, "url": "https://entreprendre.service-public.gouv.fr/x"},
                                                {}, self.page)
        reconnu = controles.controler_citation(
            "o", "d", {**verif, "url": "https://centre-national-droit-du-travail.fr/x"}, {}, self.page)
        self.assertEqual((autorite.statut, reconnu.statut), (PROUVE, PROUVE))

    def test_t2_donnees_non_versionnees_et_valeur_privee_par_defaut(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            racine = Path(d)
            subprocess.run(["git", "init", "-q"], cwd=racine, check=True)
            (racine / "s.json").write_text('{"ca": 123400}', encoding="utf-8")
            hors_git = controles.controler_citation("o", "d", {"depot": "x", "fichier": "s.json", "cle": "ca",
                                                               "min": 1}, {"x": racine})
            subprocess.run(["git", "add", "-A"], cwd=racine, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i"], cwd=racine,
                           check=True)
            versionne = controles.controler_citation("o", "d", {"depot": "x", "fichier": "s.json", "cle": "ca",
                                                                "min": 1}, {"x": racine})
        self.assertEqual(hors_git.statut, INCONNU)
        self.assertEqual(versionne.statut, INCONNU, "données internes : pas un contrôleur indépendant")
        self.assertNotIn("123400", versionne.detail + versionne.reference)

    def test_t3_un_controle_relu_ne_vaut_que_pour_la_meme_verification(self) -> None:
        import tempfile as tf

        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tf.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            p = racine / "donnees/portefeuille.toml"
            p.write_text(p.read_text(encoding="utf-8").replace(
                'demande = { note = 4, nature = "mesuré", source = "registre" }',
                'demande = { note = 4, nature = "mesuré", source = "registre", verif = { url = '
                '"https://raw.githubusercontent.com/x/y/main/note.md", contient = "marché très porteur" } }'),
                encoding="utf-8")
            # Un PROUVÉ resté en cache, obtenu pour une autre façon de vérifier la note.
            ancien = controles.Controle("citation:a/demande", "o", "portefeuille", "page-publique", "m", PROUVE,
                                        "phrase trouvée", "2099-01-01T00:00:00+00:00",
                                        "https://autre.gouv.fr/ · signature gggggggggggg", opportunite="a")
            (racine / "etat/controles.json").write_text(json.dumps([ancien.to_dict()]), encoding="utf-8")
            r = construire(racine, date(2026, 11, 24))
        self.assertEqual(next(c for c in r.controles if c.id == "citation:a/demande").statut, INCONNU)
        self.assertNotEqual(r.etats["a"]["opportunite"][0], PROUVE)

    def test_t4_t5_reseau_absent_donne_inconnu_et_jamais_zero(self) -> None:
        import tempfile as tf

        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire

        def panne(url: str) -> tuple[int, str]:
            raise OSError("réseau")
        with tf.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            with (racine / "prive/pipeline.csv").open("a", encoding="utf-8") as f:
                f.write("2026-11-23T10:00;a;r1;qualifie;email;gmail:9\n")
            r = construire(racine, date(2026, 11, 24), controler=True, lire_url=panne)
        self.assertEqual(chaine.lire(r.consolide, "a", "prospects_reels").statut, INCONNU)
        self.assertEqual(chaine.lire(r.consolide, "a", "qualifies_verifies").statut, INCONNU)
        self.assertNotIn("prospects_reels", chaine.CROISSANTS)

    def test_t6_entree_relue_inattendue_ignoree_sans_plantage(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.json"
            p.write_text(json.dumps([{"id": "citation:x", "champ_futur": 1, "objet": "o", "producteur": "a",
                                      "controleur": "b", "methode": "m", "statut": PROUVE, "detail": "d",
                                      "date": "2099-01-01T00:00:00+00:00"},
                                     {"id": "citation:y", "objet": "o", "producteur": "a", "controleur": "a",
                                      "methode": "m", "statut": PROUVE, "detail": "d", "date": "2099-01-01"}]),
                         encoding="utf-8")
            relus = controles.relire(p, ("citation:",))
        self.assertEqual([c.id for c in relus], ["citation:x"])

    def test_t7_domaines_du_second_releve_par_opportunite(self) -> None:
        import tempfile as tf

        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tf.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            p = racine / "prive/pipeline.csv"
            p.write_text("date;opportunite;ref;etape;canal;preuve;domaine\n"
                         "2026-11-21T10:00;a;r1;envoi;email;gmail:1;cabinet.fr\n", encoding="utf-8")
            # Le second relevé a vu cabinet.fr, mais pour une autre offre : cela ne prouve rien pour a.
            (racine / "prive/recomptage_messagerie.json").write_text(json.dumps(
                {"lecteur": "second-lecteur", "envois": {"a": 1}, "domaines": {"autre-offre": ["cabinet.fr"]}}),
                encoding="utf-8")
            r = construire(racine, date(2026, 11, 24), controler=True, lire_url=lambda u: (200, ""))
        prospect = next(c for c in r.controles if c.id == "prospects:a")
        self.assertEqual(prospect.statut, ECHEC)

    def test_empreintes_sans_chiffre(self) -> None:
        for texte in ("a", "page", "353561141"):
            e = controles.empreinte(texte)
            self.assertEqual((len(e), garde.fuites(e)), (12, []))
            self.assertFalse(any(ch.isdigit() for ch in e))


class QuatriemeRevue(unittest.TestCase):
    """Non-régression des brèches résiduelles trouvées par la quatrième revue indépendante (A1 à A4)."""

    page = staticmethod(lambda url: (200, "<p>Affichages ou diffusions obligatoires</p>"))
    verif = {"contient": "Affichages ou diffusions obligatoires"}

    def test_a1_le_producteur_ne_peut_pas_se_declarer_tiers(self) -> None:
        propre = controles.controler_citation("o", "d", {**self.verif, "url": "https://novarys.fr/preuve"}, {},
                                              self.page, tiers=("novarys.fr",))
        jeu = controles.controler_citation("o", "d", {**self.verif, "url": "https://www.data.gouv.fr/fr/datasets/x/"},
                                           {}, self.page)
        self.assertEqual((propre.statut, jeu.statut), (ECHEC, ECHEC))

    def test_a2_un_fichier_interne_ne_prouve_jamais_seul(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "s.json").write_text('{"n": 38}', encoding="utf-8")
            c = controles.controler_citation("o", "d", {"depot": "x", "fichier": "s.json", "cle": "n", "valeur": 38},
                                             {"x": versionner(d)})
        self.assertEqual(c.statut, INCONNU)

    def test_a3_un_controle_en_cache_n_est_jamais_prouve(self) -> None:
        import tempfile as tf

        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tf.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            p = racine / "donnees/portefeuille.toml"
            verif = {"url": "https://raw.githubusercontent.com/x/y/main/note.md", "contient": "marché très porteur"}
            p.write_text(p.read_text(encoding="utf-8").replace(
                'demande = { note = 4, nature = "mesuré", source = "registre" }',
                'demande = { note = 4, nature = "mesuré", source = "registre", verif = { url = "'
                + verif["url"] + '", contient = "' + verif["contient"] + '" } }'), encoding="utf-8")
            forge = controles.Controle("citation:a/demande", "o", "portefeuille", "page-publique", "m", PROUVE,
                                       "phrase trouvée", "2099-01-01T00:00:00+00:00",
                                       f"{verif['url']} · signature {controles.signature(verif)}", opportunite="a")
            (racine / "etat/controles.json").write_text(json.dumps([forge.to_dict()]), encoding="utf-8")
            r = construire(racine, date(2026, 11, 24))
        self.assertEqual(next(c for c in r.controles if c.id == "citation:a/demande").statut, INCONNU)
        self.assertNotEqual(r.etats["a"]["opportunite"][0], PROUVE)

    def test_a4_entrees_perimees_ou_sans_fuseau_sans_plantage(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.json"
            base = {"objet": "o", "producteur": "a", "controleur": "b", "methode": "m", "statut": PROUVE, "detail": "d"}
            p.write_text(json.dumps([{**base, "id": "citation:x", "date": "2020-01-01T00:00:00+00:00", "version": 2},
                                     {**base, "id": "citation:y", "date": "2026-11-01T10:00:00"}]), encoding="utf-8")
            relus = controles.relire(p, ("citation:",))
        self.assertEqual([(c.id, c.statut) for c in relus], [("citation:x", INCONNU), ("citation:y", INCONNU)])


class CinquiemeRevue(unittest.TestCase):
    """Non-régression : aucune étape PROUVÉE sur la seule mémoire de la mère ou les fichiers de l'auteur (B1 à B5)."""

    def racine(self, d: str) -> Path:
        from test_bout_en_bout import BoutEnBout
        return BoutEnBout().preparer(Path(d))

    def test_b1_un_rejeu_relu_ne_prouve_pas_le_produit(self) -> None:
        r = {"nom": "m", "date": "2026-11-24T00:00:00+00:00", "controleur": "mere:clone-propre", "statut": PROUVE,
             "commit": "", "bilan": "3 passed", "essais": [{"code": 0, "bilan": "3 passed"}] * 2}
        self.assertEqual(controles.controle_suite(r, None, ce_passage=False).statut, INCONNU)

    def test_b2_l_instantane_du_prestataire_ne_prouve_ni_vente_ni_encaissement(self) -> None:
        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tempfile.TemporaryDirectory() as d:
            racine = self.racine(d)
            BoutEnBout().releve_bancaire(racine)
            construire(racine, date(2026, 11, 24), lire_stripe=True, client=BoutEnBout().faux().client())
            instantane = racine / "prive/stripe.json"
            brut = json.loads(instantane.read_text(encoding="utf-8"))
            for f in brut["faits"]:
                if f["indicateur"] == "ventes_payees":
                    f["valeur"] = 3  # retouche à la main de la mémoire de la mère
            instantane.write_text(json.dumps(brut), encoding="utf-8")
            r = construire(racine, date(2026, 11, 24))
        for etape in ("vente", "encaisse", "croissance"):
            with self.subTest(etape=etape):
                self.assertNotEqual(r.etats["a"][etape][0], PROUVE)

    def test_b3_un_verdict_saisi_doit_concorder_avec_la_mesure(self) -> None:
        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tempfile.TemporaryDirectory() as d:
            racine = self.racine(d)
            prev = Path(d) / "strat/memoire/PREDICTIONS.csv"
            prev.write_text("id;date_verdict;libelle;unite;bas;central;haut;reel;sens\n"
                            "P-1;2026-11-22;x;u;1;2;3;5;plus\n", encoding="utf-8")
            p = racine / "donnees/portefeuille.toml"
            p.write_text(p.read_text(encoding="utf-8").replace('[reglages]\ndevise = "eur"',
                         '[reglages]\ndevise = "eur"\n[reglages.indicateurs_previsions]\n"P-1" = "ventes_payees"'),
                         encoding="utf-8")
            # Une vente réelle relue au prestataire ; le verdict saisi en annonce 5.
            r = construire(racine, date(2026, 11, 24), lire_stripe=True, client=BoutEnBout().faux().client())
        self.assertEqual(next(c for c in r.controles if c.id == "verdict:P-1").statut, CONFLIT)
        self.assertNotEqual(r.etats["a"]["amelioration"][0], PROUVE)

    def test_b4_sans_second_releve_aucun_acheteur_prouve(self) -> None:
        etat = chaine.etats_chaine(
            portefeuille.Opportunite("o", "o", "m", "actif", "r", "a"),
            chaine.consolider([sources.Fait("web-public", "qualifies_verifies", 1, PROUVE, "w", "o", "", "p")]), [],
            {})
        self.assertEqual(etat["acheteur"][0], INCONNU)

    def test_b5_autorites_par_hote_exact(self) -> None:
        page = lambda url: (200, "<p>Affichages ou diffusions obligatoires</p>")  # noqa: E731
        verif = {"contient": "Affichages ou diffusions obligatoires"}
        consultation = controles.controler_citation("o", "d", {**verif, "url": "https://consultation.exemple.gouv.fr/x"},
                                                    {}, page)
        officiel = controles.controler_citation("o", "d", {**verif, "url": "https://entreprendre.service-public.gouv.fr/x"},
                                                {}, page)
        self.assertEqual((consultation.statut, officiel.statut), (ECHEC, PROUVE))


class SixiemeRevue(unittest.TestCase):
    """Non-régression des deux derniers chemins de la 6ᵉ revue (C1, C2) : les fichiers de l'auteur ne prouvent rien."""

    def test_c1_un_verdict_confirme_par_un_compte_de_l_auteur_reste_inconnu(self) -> None:
        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tempfile.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            (Path(d) / "strat/memoire/PREDICTIONS.csv").write_text(
                "id;date_verdict;libelle;unite;bas;central;haut;reel;sens\nP-1;2026-11-22;x;u;1;2;3;0;plus\n",
                encoding="utf-8")
            p = racine / "donnees/portefeuille.toml"
            p.write_text(p.read_text(encoding="utf-8").replace('[reglages]\ndevise = "eur"',
                         '[reglages]\ndevise = "eur"\n[reglages.indicateurs_previsions]\n"P-1" = "reponses"'),
                         encoding="utf-8")
            r = construire(racine, date(2026, 11, 24))
        self.assertEqual(next(c for c in r.controles if c.id == "verdict:P-1").statut, INCONNU)
        self.assertNotEqual(r.etats["a"]["amelioration"][0], PROUVE)

    def test_c2_un_second_releve_fourni_a_la_main_ne_prouve_ni_prospect_ni_acheteur(self) -> None:
        from test_bout_en_bout import BoutEnBout

        from mere.tableau import construire
        with tempfile.TemporaryDirectory() as d:
            racine = BoutEnBout().preparer(Path(d))
            (racine / "prive/pipeline.csv").write_text(
                "date;opportunite;ref;etape;canal;preuve;domaine\n2026-11-21T10:00;a;r1;envoi;email;x;insee.fr\n"
                "2026-11-22T10:00;a;r1;reponse;email;x;insee.fr\n2026-11-22T11:00;a;r1;qualifie;email;x;insee.fr\n",
                encoding="utf-8")
            (racine / "prive/recomptage_messagerie.json").write_text(json.dumps(
                {"lecteur": "relecteur", "source": "lecture-directe-mere", "passage": "2026-11-24T00:00:00+00:00",
                 "envois": {"a": 1}, "reponses": 1, "rebonds": 0, "defis_antispam": 0,
                 "domaines": {"a": ["insee.fr"]}}), encoding="utf-8")
            r = construire(racine, date(2026, 11, 24), controler=True, lire_url=lambda u: (200, ""))
        self.assertEqual(next(c for c in r.controles if c.id == "pipeline:recomptage").statut, INCONNU)
        self.assertNotEqual(r.etats["a"]["acheteur"][0], PROUVE)
        self.assertNotEqual(chaine.lire(r.consolide, "a", "prospects_reels").statut, PROUVE)

