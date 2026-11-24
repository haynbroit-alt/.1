"""Attaques contre le compteur d'argent : rien d'autre qu'un paiement réel, réussi et non remboursé ne compte."""

from __future__ import annotations

import unittest
import urllib.request

from aides import FauxStripe, paiement

from mere import stripe
from mere.faits import Fait
from mere.statuts import ECHEC, INCONNU, PROUVE

OPPS = {"a": ["Produit A"], "b": ["Produit B"]}


def faits_de(r: stripe.Releve, opp: str, indicateur: str) -> Fait:
    return next(f for f in r.faits if f.opportunite == opp and f.indicateur == indicateur)


class LectureSeule(unittest.TestCase):
    def test_aucune_ecriture_possible(self) -> None:
        client = FauxStripe({}).client()
        for chemin in ("refunds", "payment_links", "customers", "invoices/in_1/send", "../v1/charges"):
            with self.subTest(chemin=chemin), self.assertRaises(PermissionError):
                client.get(chemin)

    def test_toutes_les_requetes_sont_des_get(self) -> None:
        faux = FauxStripe({"charges": [paiement("ch_1", 1000)]})
        stripe.releve(faux.client(), OPPS, opportunites=["a", "b"])
        self.assertTrue(faux.requetes)
        self.assertEqual({m for m, _ in faux.requetes}, {"GET"})

    def test_la_classe_n_expose_aucune_methode_d_ecriture(self) -> None:
        publiques = {n for n in dir(stripe.ClientLecture) if not n.startswith("_")}
        self.assertEqual(publiques, {"get", "ouvrir", "cle"})
        self.assertIsInstance(urllib.request.Request("https://x", method="GET"), urllib.request.Request)


class Comptage(unittest.TestCase):
    def releve(self, charges: list[dict], **autres: list[dict]) -> stripe.Releve:
        return stripe.releve(FauxStripe({"charges": charges, **autres}).client(), OPPS, opportunites=["a", "b"])

    def test_carte_de_test_en_mode_reel_n_est_pas_une_vente(self) -> None:
        r = self.releve([paiement("ch_t", 4900, statut="failed",
                                  outcome={"type": "invalid", "reason": "live_mode_test_card"})])
        self.assertEqual(faits_de(r, "*", "encaisse_net").valeur, 0)
        self.assertEqual(faits_de(r, "*", "ventes_payees").valeur, 0)
        echec = faits_de(r, "*", "paiements_echoues")
        self.assertEqual((echec.valeur, echec.statut), (1, ECHEC))
        self.assertIn("carte de test", echec.note)

    def test_paiement_en_mode_test_ignore(self) -> None:
        r = self.releve([paiement("ch_x", 99_900, reel=False)])
        self.assertEqual(faits_de(r, "*", "encaisse_net").valeur, 0)
        self.assertIn("mode_test", faits_de(r, "*", "encaisse_net").note)

    def test_remboursements(self) -> None:
        r = self.releve([paiement("ch_p", 10_000, rembourse=2_500, metadata={"opportunite": "a"}),
                         paiement("ch_t", 5_000, rembourse=5_000, metadata={"opportunite": "a"})])
        self.assertEqual(faits_de(r, "a", "encaisse_net").valeur, 7_500)
        self.assertEqual(faits_de(r, "a", "remboursements").valeur, 7_500)
        self.assertEqual(faits_de(r, "a", "ventes_payees").valeur, 1,
                         "un paiement remboursé en totalité n'est pas une vente")

    def test_remboursement_superieur_au_montant_borne(self) -> None:
        r = self.releve([paiement("ch_b", 1_000, rembourse=9_999, metadata={"opportunite": "a"})])
        self.assertEqual(faits_de(r, "a", "encaisse_net").valeur, 0)

    def test_autre_devise_non_additionnee(self) -> None:
        r = self.releve([paiement("ch_u", 5_000, devise="usd")])
        self.assertEqual(faits_de(r, "*", "encaisse_net").valeur, 0)
        self.assertIn("autre_devise", faits_de(r, "*", "encaisse_net").note)

    def test_facture_ouverte_est_du_ca_annonce_pas_de_l_encaisse(self) -> None:
        facture = {"id": "in_1", "status": "open", "livemode": True, "amount_due": 29_000, "lines": {"data": []}}
        r = self.releve([], invoices=[facture])
        self.assertEqual(faits_de(r, "*", "ca_annonce").valeur, 29_000)
        self.assertEqual(faits_de(r, "*", "encaisse_net").valeur, 0)

    def test_lecture_refusee_donne_inconnu_et_jamais_zero(self) -> None:
        r = stripe.releve(FauxStripe({}, refus={"charges"}).client(), OPPS, opportunites=["a"])
        enc = faits_de(r, "*", "encaisse_net")
        self.assertEqual((enc.valeur, enc.statut), (None, INCONNU))

    def test_droits_partiels_signales(self) -> None:
        r = stripe.releve(FauxStripe({"charges": []}, refus={"subscriptions", "balance_transactions"}).client(),
                          OPPS, opportunites=["a"])
        self.assertEqual(faits_de(r, "*", "abonnements_actifs").statut, INCONNU)
        self.assertEqual(faits_de(r, "*", "frais_paiement").statut, INCONNU)
        self.assertEqual(faits_de(r, "*", "encaisse_net").statut, PROUVE)

    def test_pagination_complete(self) -> None:
        charges = [paiement(f"ch_{i:03d}", 100, metadata={"opportunite": "a"}) for i in range(250)]
        faux = FauxStripe({"charges": charges}, page=100)
        r = stripe.releve(faux.client(), OPPS, opportunites=["a"])
        self.assertEqual(faits_de(r, "a", "encaisse_net").valeur, 25_000)
        self.assertEqual(sum(1 for _, u in faux.requetes if "/charges" in u), 3)

    def test_pagination_sans_fin_refusee(self) -> None:
        charges = [paiement(f"ch_{i:04d}", 1) for i in range(60)]
        client = FauxStripe({"charges": charges}, page=1).client()
        with self.assertRaises(stripe.LectureImpossible):
            stripe.lister(client, "charges", pages_max=10)


class Attribution(unittest.TestCase):
    def test_par_produit_de_facture(self) -> None:
        donnees = {"charges": [paiement("ch_f", 3_900, invoice="in_9")],
                   "products": [{"id": "prod_B1234567", "name": "Produit B mensuel", "active": True}],
                   "invoices": [{"id": "in_9", "status": "paid", "livemode": True, "amount_due": 3_900,
                                 "lines": {"data": [{"price": {"product": "prod_B1234567"}}]}}]}
        r = stripe.releve(FauxStripe(donnees).client(), OPPS, opportunites=["a", "b"])
        self.assertEqual(faits_de(r, "b", "encaisse_net").valeur, 3_900)
        self.assertEqual(faits_de(r, "a", "encaisse_net").valeur, 0)

    def test_paiement_non_attribue_rend_les_autres_inconnus(self) -> None:
        r = stripe.releve(FauxStripe({"charges": [paiement("ch_n", 5_000, description="divers")]}).client(),
                          OPPS, opportunites=["a", "b"])
        self.assertEqual(faits_de(r, stripe.NON_ATTRIBUE, "encaisse_net").valeur, 5_000)
        self.assertEqual(faits_de(r, "a", "encaisse_net").statut, INCONNU)
        self.assertEqual(faits_de(r, "*", "encaisse_net").valeur, 5_000)

    def test_metadonnee_inconnue_ignoree(self) -> None:
        r = stripe.releve(FauxStripe({"charges": [paiement("ch_m", 100, metadata={"opportunite": "pirate"})]}).client(),
                          OPPS, opportunites=["a"])
        self.assertFalse(any(f.opportunite == "pirate" for f in r.faits))


if __name__ == "__main__":
    unittest.main()
