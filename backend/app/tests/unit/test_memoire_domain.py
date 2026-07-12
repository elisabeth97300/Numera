import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.memoire_domain import (  # noqa: E402
    HistoriqueTiers,
    combiner_confiance,
    normaliser_tiers,
    suggerer_depuis_memoire,
)


class TestNormaliserTiers(unittest.TestCase):
    def test_casse_et_accents_normalises(self):
        self.assertEqual(normaliser_tiers("AMAZON EU"), normaliser_tiers("Amazon eu"))

    def test_suffixe_juridique_retire(self):
        self.assertEqual(normaliser_tiers("Amazon EU Sarl"), normaliser_tiers("Amazon EU"))

    def test_ponctuation_ignoree(self):
        self.assertEqual(normaliser_tiers("EDF, entreprises"), normaliser_tiers("EDF entreprises"))


class TestSuggererDepuisMemoire(unittest.TestCase):
    def test_aucun_historique_retourne_none(self):
        self.assertIsNone(suggerer_depuis_memoire("Amazon", []))

    def test_habitude_forte_confiance_haute(self):
        historiques = [HistoriqueTiers("amazon", "606300", nombre_confirmations=5)]
        suggestion = suggerer_depuis_memoire("Amazon", historiques)
        self.assertEqual(suggestion.compte_pcg, "606300")
        self.assertGreaterEqual(suggestion.confiance, 0.9)

    def test_habitude_unique_faible_confiance_moyenne(self):
        historiques = [HistoriqueTiers("amazon", "606300", nombre_confirmations=1)]
        suggestion = suggerer_depuis_memoire("Amazon", historiques)
        self.assertAlmostEqual(suggestion.confiance, 0.6)

    def test_comptes_incoherents_confiance_reduite(self):
        historiques = [
            HistoriqueTiers("amazon", "606300", nombre_confirmations=3),
            HistoriqueTiers("amazon", "618300", nombre_confirmations=3),
        ]
        suggestion = suggerer_depuis_memoire("Amazon", historiques)
        self.assertLess(suggestion.confiance, 0.5)


class TestCombinerConfiance(unittest.TestCase):
    def test_memoire_forte_et_accord_llm_autorise_auto_validation(self):
        memoire = suggerer_depuis_memoire("Amazon", [HistoriqueTiers("amazon", "606300", 5)])
        decision = combiner_confiance(confiance_ocr=0.9, confiance_llm=0.85, suggestion_memoire=memoire, compte_propose_llm="606300")
        self.assertTrue(decision.peut_auto_valider)
        self.assertEqual(decision.source_principale, "memoire+llm_accord")

    def test_memoire_forte_mais_desaccord_llm_bloque_auto_validation(self):
        memoire = suggerer_depuis_memoire("Amazon", [HistoriqueTiers("amazon", "606300", 5)])
        decision = combiner_confiance(confiance_ocr=0.9, confiance_llm=0.85, suggestion_memoire=memoire, compte_propose_llm="618300")
        self.assertFalse(decision.peut_auto_valider)
        self.assertEqual(decision.source_principale, "conflit_memoire_llm")

    def test_sans_memoire_moyenne_ponderee_ocr_llm(self):
        decision = combiner_confiance(confiance_ocr=1.0, confiance_llm=0.5, suggestion_memoire=None, compte_propose_llm="606300")
        self.assertAlmostEqual(decision.confiance_finale, 0.4 * 1.0 + 0.6 * 0.5)
        self.assertFalse(decision.peut_auto_valider)

    def test_ocr_faible_bloque_auto_validation_meme_avec_memoire_forte(self):
        memoire = suggerer_depuis_memoire("Amazon", [HistoriqueTiers("amazon", "606300", 5)])
        decision = combiner_confiance(confiance_ocr=0.3, confiance_llm=0.9, suggestion_memoire=memoire, compte_propose_llm="606300")
        self.assertFalse(decision.peut_auto_valider)


if __name__ == "__main__":
    unittest.main()
