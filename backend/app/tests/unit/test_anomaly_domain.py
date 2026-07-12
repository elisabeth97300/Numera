import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.anomaly_domain import (  # noqa: E402
    EcritureComparable,
    TypeAnomalie,
    detecter_date_hors_exercice,
    detecter_doublons_probables,
    detecter_taux_tva_inconnu,
)


class TestDoublonsProbables(unittest.TestCase):
    def test_meme_tiers_meme_montant_dates_proches_detecte(self):
        ecritures = [
            EcritureComparable("e1", "EDF", Decimal("221.04"), date(2026, 7, 4)),
            EcritureComparable("e2", "edf", Decimal("221.04"), date(2026, 7, 5)),  # casse différente, 1 jour d'écart
        ]
        anomalies = detecter_doublons_probables(ecritures)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].type, TypeAnomalie.DOUBLON_PROBABLE)

    def test_tiers_different_non_detecte(self):
        ecritures = [
            EcritureComparable("e1", "EDF", Decimal("221.04"), date(2026, 7, 4)),
            EcritureComparable("e2", "Engie", Decimal("221.04"), date(2026, 7, 4)),
        ]
        self.assertEqual(detecter_doublons_probables(ecritures), [])

    def test_montant_trop_different_non_detecte(self):
        ecritures = [
            EcritureComparable("e1", "EDF", Decimal("221.04"), date(2026, 7, 4)),
            EcritureComparable("e2", "EDF", Decimal("300.00"), date(2026, 7, 4)),
        ]
        self.assertEqual(detecter_doublons_probables(ecritures), [])

    def test_dates_trop_eloignees_non_detecte(self):
        ecritures = [
            EcritureComparable("e1", "EDF", Decimal("221.04"), date(2026, 7, 4)),
            EcritureComparable("e2", "EDF", Decimal("221.04"), date(2026, 8, 4)),
        ]
        self.assertEqual(detecter_doublons_probables(ecritures), [])

    def test_trois_ecritures_ne_genere_pas_de_doublons_avec_soi_meme(self):
        ecritures = [
            EcritureComparable("e1", "EDF", Decimal("100"), date(2026, 7, 1)),
            EcritureComparable("e2", "Engie", Decimal("200"), date(2026, 7, 2)),
            EcritureComparable("e3", "Free", Decimal("300"), date(2026, 7, 3)),
        ]
        self.assertEqual(detecter_doublons_probables(ecritures), [])


class TestDateHorsExercice(unittest.TestCase):
    def test_date_dans_exercice_ne_leve_rien(self):
        resultat = detecter_date_hors_exercice("e1", date(2026, 6, 1), date(2026, 1, 1), date(2026, 12, 31))
        self.assertIsNone(resultat)

    def test_date_avant_exercice_detectee(self):
        resultat = detecter_date_hors_exercice("e1", date(2025, 12, 31), date(2026, 1, 1), date(2026, 12, 31))
        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.type, TypeAnomalie.DATE_HORS_EXERCICE)

    def test_date_apres_exercice_detectee(self):
        resultat = detecter_date_hors_exercice("e1", date(2027, 1, 1), date(2026, 1, 1), date(2026, 12, 31))
        self.assertIsNotNone(resultat)


class TestTauxTVA(unittest.TestCase):
    def test_taux_legal_ne_leve_rien(self):
        self.assertIsNone(detecter_taux_tva_inconnu("e1", Decimal("20")))
        self.assertIsNone(detecter_taux_tva_inconnu("e1", Decimal("5.5")))

    def test_taux_inconnu_detecte(self):
        resultat = detecter_taux_tva_inconnu("e1", Decimal("15"))
        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.type, TypeAnomalie.TAUX_TVA_INCONNU)


if __name__ == "__main__":
    unittest.main()
