"""De bout en bout, sur un écosystème factice : sources lues, argent rapproché, sorties publiques sans fuite."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from aides import FauxStripe, paiement

from mere import garde
from mere.__main__ import main
from mere.tableau import construire, rendre

SOURCES = """
[depots]
strat = ["../strat"]
novarys = ["../absent"]
[fichiers]
previsions = { depot = "strat", chemin = "memoire/PREDICTIONS.csv" }
tableau_novarys = { depot = "strat", chemin = "tableau.toml" }
pipeline = { chemin = "prive/pipeline.csv" }
couts = { chemin = "prive/couts.csv" }
"""

PORTEFEUILLE = """
[reglages]
devise = "eur"
[[opportunite]]
id = "a"
nom = "Offre A"
module = "strat"
statut = "actif"
responsable = "propriétaire"
prochaine_action = "{action}"
stripe_produits = ["Produit A"]
previsions = ["P-1"]
declare = {{ depot = "strat", fichier = "memoire/PROJETS.md", ligne = "Offre A" }}
[opportunite.criteres]
demande = {{ note = 4, nature = "mesuré", source = "registre" }}
concurrence = {{ note = 2, nature = "hypothèse" }}
marge = {{ note = 4, nature = "calcul", source = "calcul" }}
cac = {{ note = 1, nature = "hypothèse" }}
vitesse = {{ note = 1, nature = "hypothèse" }}
potentiel = {{ note = 5, nature = "hypothèse" }}
[[opportunite.arret]]
libelle = "une réponse"
indicateur = "reponses"
seuil = 1
date = "2026-11-20"
si_echec = "changer de canal"
"""


class BoutEnBout(unittest.TestCase):
    def preparer(self, d: Path, action: str = "relancer") -> Path:
        racine = d / "mere"
        for sous in ("donnees", "prive", "etat"):
            (racine / sous).mkdir(parents=True)
        (d / "strat/memoire").mkdir(parents=True)
        (racine / "donnees/sources.toml").write_text(SOURCES, encoding="utf-8")
        (racine / "donnees/portefeuille.toml").write_text(PORTEFEUILLE.format(action=action), encoding="utf-8")
        (racine / "prive/pipeline.csv").write_text(
            "date;opportunite;ref;etape;canal;preuve\n2026-11-21T10:00;a;r1;envoi;email;gmail:1\n"
            "2026-11-22T10:00;a;r2;envoi;email;gmail:2\n", encoding="utf-8")
        (d / "strat/memoire/PREDICTIONS.csv").write_text(
            "id;date_verdict;libelle;unite;bas;central;haut;reel;sens\nP-1;2026-11-22;x;u;1;2;3;;plus\n",
            encoding="utf-8")
        (d / "strat/memoire/PROJETS.md").write_text("| Projet | Statut |\n|---|---|\n| Offre A (x) | Gelé |\n",
                                                    encoding="utf-8")
        (d / "strat/tableau.toml").write_text('[[measure]]\nlabel = "Encaissé"\nvalue = "0 €"\n'
                                              'source = "relevé le 23/11/2026"\n', encoding="utf-8")
        return racine

    def faux(self, verse: bool = True) -> FauxStripe:
        charge = paiement("ch_vrai000001", 1_234_500, metadata={"opportunite": "a"}, cree=1_795_300_000)
        return FauxStripe({
            "charges": [charge],
            "products": [{"id": "prod_A0000001", "name": "Produit A", "active": True, "livemode": True}],
            "prices": [{"id": "price_A000001", "product": "prod_A0000001", "active": True, "livemode": True}],
            "balance_transactions": [{"id": "txn_A0000001", "type": "charge", "source": "ch_vrai000001",
                                      "amount": 1_234_500, "fee": 18_500}],
            "payouts": [{"id": "po_A00000001", "status": "paid", "livemode": True, "amount": 1_216_000,
                         "arrival_date": 1_795_500_000}] if verse else [],
        })

    def releve_bancaire(self, racine: Path) -> None:
        (racine / "prive/banque.csv").write_text("date;libelle;montant;reference\n2026-11-24;VIREMENT;12160,00;x\n",
                                                encoding="utf-8")

    def test_chaine_complete(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self.preparer(Path(d))
            self.releve_bancaire(racine)
            r = construire(racine, date(2026, 11, 24), lire_stripe=True, client=self.faux().client())
            public, prive = rendre(r, prive=False), rendre(r, prive=True)
        self.assertEqual(r.erreurs, [])
        self.assertEqual(garde.fuites(public), [], "la sortie publique doit être publiable")
        self.assertIn("Premier euro : atteint", public)
        self.assertNotIn("12 345", public)
        self.assertIn("12 345,00 €", prive)
        etats = r.etats["a"]
        self.assertEqual(etats["encaisse"][0], "PROUVÉ")
        self.assertEqual(etats["acheteur"][0], "ÉCHEC", "aucune réponse à la date du critère")
        self.assertEqual(etats["amelioration"][0], "ÉCHEC", "prévision échue sans résultat")
        textes = " ".join(r.conflits)
        self.assertIn("gele", textes, "registre qui déclare gelé une offre qui prospecte")
        self.assertIn("encaissé différent", textes, "portail qui déclare 0 € après un paiement")
        self.assertIn("| Bénéfice net (hors temps) | — | INCONNU |", public, "un coût inconnu n'est jamais compté nul")

    def test_paiement_sans_releve_bancaire_n_est_pas_un_encaissement_prouve(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self.preparer(Path(d))
            r = construire(racine, date(2026, 11, 24), lire_stripe=True, client=self.faux().client())
        self.assertIn("Premier euro : INCONNU : paiement réussi, mais crédit en banque non vérifié", rendre(r, False))
        self.assertEqual(r.etats["a"]["encaisse"][0], "INCONNU")

    def test_virement_absent_du_releve_est_un_conflit(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self.preparer(Path(d))
            (racine / "prive/banque.csv").write_text("date;libelle;montant\n2026-11-24;AUTRE;10,00\n", encoding="utf-8")
            r = construire(racine, date(2026, 11, 24), lire_stripe=True, client=self.faux().client())
        banque = next(c for c in r.controles if c.id == "argent:credite-en-banque")
        self.assertEqual(banque.statut, "CONFLIT")

    def test_rien_de_public_n_est_ecrit_par_construire(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self.preparer(Path(d))
            avant = sorted(p.name for p in (racine / "etat").iterdir())
            construire(racine, date(2026, 11, 24), lire_stripe=True, client=self.faux().client())
            self.assertEqual(sorted(p.name for p in (racine / "etat").iterdir()), avant)

    def test_recomptage_independant_qui_trouve_un_rebond_manque(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self.preparer(Path(d))
            (racine / "prive/recomptage_messagerie.json").write_text(
                '{"lecteur": "second-lecteur", "envois": {"a": 2}, "reponses": 0, "rebonds": 1}', encoding="utf-8")
            r = construire(racine, date(2026, 11, 24))
            recompte = next(c for c in r.controles if c.id == "pipeline:recomptage")
            self.assertEqual(recompte.statut, "CONFLIT")
            self.assertIn("rebonds", recompte.detail)
            with (racine / "prive/pipeline.csv").open("a", encoding="utf-8") as f:
                f.write("2026-11-22T11:00;a;r2;rebond;email;gmail:3\n")
            r = construire(racine, date(2026, 11, 24))
        self.assertEqual(next(c for c in r.controles if c.id == "pipeline:recomptage").statut, "PROUVÉ")

    def test_fuite_refusee(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self.preparer(Path(d), action="écrire à prenom.nom@client.fr")
            r = construire(racine, date(2026, 11, 24), lire_stripe=True, client=self.faux().client())
        self.assertTrue(garde.fuites(rendre(r, prive=False)))

    def test_sans_prestataire_rien_n_est_prouve(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            racine = self.preparer(Path(d))
            r = construire(racine, date(2026, 11, 24))
        self.assertIn("Premier euro : INCONNU", rendre(r, prive=False))


class DepotReel(unittest.TestCase):
    def test_verifier_le_depot(self) -> None:
        self.assertEqual(main(["verifier"]), 0)


if __name__ == "__main__":
    unittest.main()
