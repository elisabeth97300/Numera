import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.ecriture_domain import (  # noqa: E402
    EcritureError,
    LigneEcritureDomaine,
    construire_ecriture_depuis_proposition,
    extourner,
    valider_equilibre,
)


class TestLigneEcriture(unittest.TestCase):
    def test_ligne_debit_et_credit_simultanes_refusee(self):
        with self.assertRaises(EcritureError):
            LigneEcritureDomaine("606100", "test", debit=Decimal("10"), credit=Decimal("10"))

    def test_ligne_montant_nul_refusee(self):
        with self.assertRaises(EcritureError):
            LigneEcritureDomaine("606100", "test")

    def test_ligne_montant_negatif_refusee(self):
        with self.assertRaises(EcritureError):
            LigneEcritureDomaine("606100", "test", debit=Decimal("-5"))


class TestEquilibre(unittest.TestCase):
    def test_ecriture_equilibree_ne_leve_rien(self):
        lignes = [
            LigneEcritureDomaine("606100", "charge", debit=Decimal("100")),
            LigneEcritureDomaine("401000", "fournisseur", credit=Decimal("100")),
        ]
        valider_equilibre(lignes)

    def test_ecriture_desequilibree_refusee(self):
        lignes = [
            LigneEcritureDomaine("606100", "charge", debit=Decimal("100")),
            LigneEcritureDomaine("401000", "fournisseur", credit=Decimal("90")),
        ]
        with self.assertRaises(EcritureError):
            valider_equilibre(lignes)

    def test_une_seule_ligne_refusee(self):
        with self.assertRaises(EcritureError):
            valider_equilibre([LigneEcritureDomaine("606100", "charge", debit=Decimal("100"))])


class TestExtourne(unittest.TestCase):
    def test_extourne_inverse_debit_et_credit(self):
        lignes = [
            LigneEcritureDomaine("606100", "charge", debit=Decimal("100")),
            LigneEcritureDomaine("401000", "fournisseur", credit=Decimal("100")),
        ]
        extourne = extourner(lignes)
        self.assertEqual(extourne[0].credit, Decimal("100"))
        self.assertEqual(extourne[0].debit, Decimal("0"))
        self.assertEqual(extourne[1].debit, Decimal("100"))
        self.assertTrue(extourne[0].libelle.startswith("Extourne"))
        valider_equilibre(extourne)  # une extourne doit rester équilibrée


class TestConstructionDepuisProposition(unittest.TestCase):
    def test_facture_avec_tva_genere_trois_lignes_equilibrees(self):
        lignes = construire_ecriture_depuis_proposition(
            compte_charge_ou_produit="606100",
            compte_tva="445660",
            compte_tiers="401000",
            tiers="EDF",
            montant_ht=Decimal("184.20"),
            montant_tva=Decimal("36.84"),
            libelle_base="Facture EDF juillet",
        )
        self.assertEqual(len(lignes), 3)
        total_debit = sum(l.debit for l in lignes)
        total_credit = sum(l.credit for l in lignes)
        self.assertEqual(total_debit, total_credit)
        self.assertEqual(total_credit, Decimal("221.04"))

    def test_facture_sans_tva_genere_deux_lignes(self):
        lignes = construire_ecriture_depuis_proposition(
            compte_charge_ou_produit="606100",
            compte_tva=None,
            compte_tiers="401000",
            tiers="Association loi 1901",
            montant_ht=Decimal("50.00"),
            montant_tva=Decimal("0"),
            libelle_base="Cotisation",
        )
        self.assertEqual(len(lignes), 2)

    def test_tva_sans_compte_tva_leve_une_erreur(self):
        with self.assertRaises(EcritureError):
            construire_ecriture_depuis_proposition(
                compte_charge_ou_produit="606100",
                compte_tva=None,
                compte_tiers="401000",
                tiers="EDF",
                montant_ht=Decimal("100"),
                montant_tva=Decimal("20"),
                libelle_base="test",
            )


if __name__ == "__main__":
    unittest.main()
