import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.pilotage_domain import (  # noqa: E402
    MouvementClient,
    PosteComparatif,
    calculer_rentabilite_clients,
    comparer_resultats,
)


class TestRentabiliteClients(unittest.TestCase):
    def test_tri_du_moins_au_plus_rentable(self):
        mouvements = [
            MouvementClient("Client A", chiffre_affaires=Decimal("10000"), charges_attribuables=Decimal("2000")),
            MouvementClient("Client B", chiffre_affaires=Decimal("3000"), charges_attribuables=Decimal("2800")),
        ]
        resultats = calculer_rentabilite_clients(mouvements)
        self.assertEqual(resultats[0].tiers, "Client B")  # marge la plus faible en premier
        self.assertEqual(resultats[0].marge_estimee, Decimal("200"))
        self.assertEqual(resultats[1].tiers, "Client A")

    def test_cumul_de_plusieurs_mouvements_pour_le_meme_client(self):
        mouvements = [
            MouvementClient("Client A", chiffre_affaires=Decimal("1000")),
            MouvementClient("Client A", chiffre_affaires=Decimal("500")),
        ]
        resultats = calculer_rentabilite_clients(mouvements)
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0].chiffre_affaires, Decimal("1500"))


class TestComparerResultats(unittest.TestCase):
    def test_charges_en_hausse_triees_par_ampleur(self):
        charges = [
            PosteComparatif("606100", montant_courant=Decimal("1000"), montant_precedent=Decimal("900")),
            PosteComparatif("613000", montant_courant=Decimal("5000"), montant_precedent=Decimal("2000")),
            PosteComparatif("622600", montant_courant=Decimal("500"), montant_precedent=Decimal("600")),  # en baisse
        ]
        produits = []
        comparaison = comparer_resultats(charges, produits, Decimal("8000"), Decimal("10000"))
        self.assertEqual(len(comparaison.charges_en_hausse), 2)
        self.assertEqual(comparaison.charges_en_hausse[0].compte_pcg, "613000")  # plus grosse hausse en premier
        self.assertEqual(comparaison.variation_resultat(), Decimal("-2000"))

    def test_produits_en_baisse_identifies(self):
        produits = [
            PosteComparatif("706000", montant_courant=Decimal("8000"), montant_precedent=Decimal("12000")),
            PosteComparatif("706100", montant_courant=Decimal("3000"), montant_precedent=Decimal("2000")),  # en hausse
        ]
        comparaison = comparer_resultats([], produits, Decimal("5000"), Decimal("6000"))
        self.assertEqual(len(comparaison.produits_en_baisse), 1)
        self.assertEqual(comparaison.produits_en_baisse[0].compte_pcg, "706000")


if __name__ == "__main__":
    unittest.main()
