import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # backend/

from app.domain.exercice_domain import LigneSolde, SourceSolde  # noqa: E402
from app.domain.reporting_domain import (  # noqa: E402
    MouvementCompte,
    calculer_ratios,
    construire_balance,
    construire_bilan,
    construire_compte_resultat,
)


class TestConstruireBalance(unittest.TestCase):
    def test_solde_ouverture_plus_mouvements_cumules(self):
        solde_ouverture = [LigneSolde("512000", solde_debit=Decimal("1000"), source=SourceSolde.SAISIE_MANUELLE)]
        mouvements = [
            MouvementCompte("512000", debit=Decimal("500"), credit=Decimal("0")),
            MouvementCompte("512000", debit=Decimal("0"), credit=Decimal("200")),
        ]
        balance = construire_balance(solde_ouverture, mouvements)
        compte = next(b for b in balance if b.compte_pcg == "512000")
        self.assertEqual(compte.total_debit, Decimal("1500"))
        self.assertEqual(compte.total_credit, Decimal("200"))
        self.assertEqual(compte.solde(), Decimal("1300"))

    def test_compte_sans_solde_ouverture_uniquement_mouvements(self):
        balance = construire_balance([], [MouvementCompte("606100", debit=Decimal("100"), credit=Decimal("0"))])
        self.assertEqual(len(balance), 1)
        self.assertEqual(balance[0].total_debit, Decimal("100"))


class TestBilan(unittest.TestCase):
    def test_classement_actif_et_passif(self):
        from app.domain.exercice_domain import BalanceCompte

        balance = [
            BalanceCompte("512000", total_debit=Decimal("10000"), total_credit=Decimal("2000")),  # banque -> actif
            BalanceCompte("401000", total_debit=Decimal("0"), total_credit=Decimal("4000")),  # fournisseurs -> passif
            BalanceCompte("101000", total_debit=Decimal("0"), total_credit=Decimal("4000")),  # capital -> passif
        ]
        bilan = construire_bilan(balance)
        self.assertEqual(len(bilan.actif), 1)
        self.assertEqual(len(bilan.passif), 2)
        self.assertEqual(bilan.total_actif(), Decimal("8000"))
        self.assertEqual(bilan.total_passif(), Decimal("8000"))
        self.assertTrue(bilan.est_equilibre())

    def test_comptes_de_gestion_absents_du_bilan(self):
        from app.domain.exercice_domain import BalanceCompte

        balance = [BalanceCompte("606100", total_debit=Decimal("500"), total_credit=Decimal("0"))]
        bilan = construire_bilan(balance)
        self.assertEqual(bilan.actif, [])
        self.assertEqual(bilan.passif, [])


class TestCompteResultat(unittest.TestCase):
    def test_charges_et_produits_correctement_calcules(self):
        from app.domain.exercice_domain import BalanceCompte

        balance = [
            BalanceCompte("606100", total_debit=Decimal("3000"), total_credit=Decimal("0")),
            BalanceCompte("706000", total_debit=Decimal("0"), total_credit=Decimal("9000")),
        ]
        cr = construire_compte_resultat(balance)
        self.assertEqual(cr.total_charges(), Decimal("3000"))
        self.assertEqual(cr.total_produits(), Decimal("9000"))
        self.assertEqual(cr.resultat_net(), Decimal("6000"))


class TestRatios(unittest.TestCase):
    def test_taux_marge_calcule(self):
        from app.domain.reporting_domain import CompteResultat, PosteBilan

        cr = CompteResultat(
            charges=[PosteBilan("606100", "Charge", Decimal("3000"))],
            produits=[PosteBilan("706000", "Produit", Decimal("9000"))],
        )
        ratios = calculer_ratios(cr)
        self.assertEqual(ratios.resultat_net, Decimal("6000"))
        self.assertAlmostEqual(float(ratios.taux_marge), 66.666, places=2)

    def test_taux_marge_none_si_aucun_produit(self):
        from app.domain.reporting_domain import CompteResultat

        cr = CompteResultat(charges=[], produits=[])
        ratios = calculer_ratios(cr)
        self.assertIsNone(ratios.taux_marge)


if __name__ == "__main__":
    unittest.main()
