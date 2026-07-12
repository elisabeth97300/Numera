import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/app/

from domain.reconciliation_domain import parser_csv_releve  # noqa: E402


class TestParserCSVReleve(unittest.TestCase):
    def test_format_standard_avec_entete(self):
        contenu = (
            "date;libelle;montant\n"
            "04/07/2026;VIR EDF;-221.04\n"
            "05/07/2026;VIR CLIENT DUPONT;1500,00\n"
        ).encode("utf-8")
        lignes = parser_csv_releve(contenu)
        self.assertEqual(len(lignes), 2)
        self.assertEqual(lignes[0], (date(2026, 7, 4), "VIR EDF", Decimal("-221.04")))
        self.assertEqual(lignes[1], (date(2026, 7, 5), "VIR CLIENT DUPONT", Decimal("1500.00")))

    def test_format_date_iso(self):
        contenu = "date;libelle;montant\n2026-07-04;VIR EDF;-221.04\n".encode("utf-8")
        lignes = parser_csv_releve(contenu)
        self.assertEqual(lignes[0][0], date(2026, 7, 4))

    def test_virgule_decimale_normalisee(self):
        contenu = "date;libelle;montant\n04/07/2026;TEST;1 234,56\n".encode("utf-8")
        lignes = parser_csv_releve(contenu)
        self.assertEqual(lignes[0][2], Decimal("1234.56"))

    def test_ligne_illisible_ignoree_sans_faire_echouer_tout_le_fichier(self):
        contenu = (
            "date;libelle;montant\n"
            "04/07/2026;OK;100.00\n"
            "date-invalide;CASSE;abc\n"
            "06/07/2026;OK2;200.00\n"
        ).encode("utf-8")
        lignes = parser_csv_releve(contenu)
        self.assertEqual(len(lignes), 2)

    def test_fichier_vide_retourne_liste_vide(self):
        self.assertEqual(parser_csv_releve(b""), [])


if __name__ == "__main__":
    unittest.main()
