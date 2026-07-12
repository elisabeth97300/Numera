import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.depenses_domain import identifier_depenses_reductibles  # noqa: E402


class TestIdentifierDepensesReductibles(unittest.TestCase):
    def test_compte_compressible_identifie(self):
        comptes = {"625600": Decimal("3000")}  # missions et réceptions
        suggestions = identifier_depenses_reductibles(comptes)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].compte_pcg, "625600")

    def test_compte_structurel_exclu(self):
        comptes = {"641000": Decimal("50000")}  # salaires
        suggestions = identifier_depenses_reductibles(comptes)
        self.assertEqual(suggestions, [])

    def test_tri_par_montant_decroissant(self):
        comptes = {"618200": Decimal("500"), "613500": Decimal("2000")}
        suggestions = identifier_depenses_reductibles(comptes)
        self.assertEqual(suggestions[0].compte_pcg, "613500")
        self.assertEqual(suggestions[1].compte_pcg, "618200")

    def test_compte_inconnu_ignore(self):
        comptes = {"999999": Decimal("100")}
        self.assertEqual(identifier_depenses_reductibles(comptes), [])

    def test_montant_negatif_ou_nul_ignore(self):
        comptes = {"613500": Decimal("0"), "618200": Decimal("-50")}
        self.assertEqual(identifier_depenses_reductibles(comptes), [])

    def test_prefixe_plus_specifique_prioritaire(self):
        # 6247 (transport de personnel, compressible) vs un préfixe générique 62 non défini
        comptes = {"624700": Decimal("800")}
        suggestions = identifier_depenses_reductibles(comptes)
        self.assertEqual(suggestions[0].libelle, "Transports de personnel")


if __name__ == "__main__":
    unittest.main()
