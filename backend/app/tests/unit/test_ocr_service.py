import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # backend/

from app.services.ocr_service import analyser_texte  # noqa: E402


class TestAnalyserTexte(unittest.TestCase):
    def test_facture_type_extrait_montant_et_date(self):
        texte = """
        EDF ENTREPRISES
        Facture n° 2026-0456
        Date : 04/07/2026
        Montant HT : 184.20
        TVA 20% : 36.84
        Total TTC : 221.04
        """
        resultat = analyser_texte(texte)
        noms = {c.nom: c.valeur for c in resultat.champs}
        self.assertEqual(noms.get("montant_ttc"), "221.04")
        self.assertEqual(noms.get("montant_tva"), "36.84")
        self.assertEqual(noms.get("date"), "04/07/2026")

    def test_texte_sans_montant_ne_leve_pas_et_renvoie_peu_de_champs(self):
        resultat = analyser_texte("texte illisible sans structure reconnaissable")
        self.assertEqual(resultat.champs, [])

    def test_virgule_decimale_normalisee_en_point(self):
        texte = "Total TTC : 1234,56 euros"
        resultat = analyser_texte(texte)
        montant = next(c for c in resultat.champs if c.nom == "montant_ttc")
        self.assertEqual(montant.valeur, "1234.56")


if __name__ == "__main__":
    unittest.main()
