import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.tva_domain import LigneTVA, preparer_tva  # noqa: E402


class TestPreparerTVA(unittest.TestCase):
    def test_ventilation_par_taux_et_solde_a_payer(self):
        lignes = [
            LigneTVA("706000", Decimal("20"), Decimal("1000"), Decimal("200"), "collectee"),
            LigneTVA("706100", Decimal("10"), Decimal("500"), Decimal("50"), "collectee"),
            LigneTVA("606100", Decimal("20"), Decimal("400"), Decimal("80"), "deductible"),
        ]
        prep = preparer_tva(lignes)

        self.assertEqual(len(prep.collectee_par_taux), 2)
        self.assertEqual(prep.total_collectee(), Decimal("250"))
        self.assertEqual(prep.total_deductible(), Decimal("80"))
        self.assertEqual(prep.solde_a_payer(), Decimal("170"))

    def test_deux_lignes_meme_taux_cumulees(self):
        lignes = [
            LigneTVA("706000", Decimal("20"), Decimal("1000"), Decimal("200"), "collectee"),
            LigneTVA("706050", Decimal("20"), Decimal("500"), Decimal("100"), "collectee"),
        ]
        prep = preparer_tva(lignes)
        self.assertEqual(len(prep.collectee_par_taux), 1)
        self.assertEqual(prep.collectee_par_taux[0].montant_tva, Decimal("300"))

    def test_credit_de_tva_si_deductible_superieure(self):
        lignes = [
            LigneTVA("706000", Decimal("20"), Decimal("100"), Decimal("20"), "collectee"),
            LigneTVA("606100", Decimal("20"), Decimal("1000"), Decimal("200"), "deductible"),
        ]
        prep = preparer_tva(lignes)
        self.assertTrue(prep.solde_a_payer() < 0)


if __name__ == "__main__":
    unittest.main()
