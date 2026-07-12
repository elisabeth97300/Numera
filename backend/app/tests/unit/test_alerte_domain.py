import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.alerte_domain import (  # noqa: E402
    NiveauAlerte,
    alerte_anomalies,
    alerte_exercice_proche_cloture,
    alerte_risque_tresorerie,
    alerte_tva_a_payer,
    prioriser_alertes,
)


class TestAlerteTresorerie(unittest.TestCase):
    def test_scenario_pessimiste_negatif_declenche_alerte_urgente(self):
        alerte = alerte_risque_tresorerie(Decimal("-500"), 90)
        self.assertIsNotNone(alerte)
        self.assertEqual(alerte.niveau, NiveauAlerte.URGENT)

    def test_scenario_pessimiste_positif_aucune_alerte(self):
        self.assertIsNone(alerte_risque_tresorerie(Decimal("500"), 90))


class TestAlerteAnomalies(unittest.TestCase):
    def test_aucune_anomalie_aucune_alerte(self):
        self.assertIsNone(alerte_anomalies(0))

    def test_peu_anomalies_niveau_attention(self):
        alerte = alerte_anomalies(2)
        self.assertEqual(alerte.niveau, NiveauAlerte.ATTENTION)

    def test_beaucoup_anomalies_niveau_urgent(self):
        alerte = alerte_anomalies(10)
        self.assertEqual(alerte.niveau, NiveauAlerte.URGENT)


class TestAlerteTVA(unittest.TestCase):
    def test_pas_de_tva_a_payer_aucune_alerte(self):
        self.assertIsNone(alerte_tva_a_payer(Decimal("-100"), date(2026, 8, 1), date(2026, 7, 10)))

    def test_echeance_lointaine_aucune_alerte(self):
        self.assertIsNone(alerte_tva_a_payer(Decimal("500"), date(2026, 12, 1), date(2026, 7, 10)))

    def test_echeance_proche_alerte_attention(self):
        alerte = alerte_tva_a_payer(Decimal("500"), date(2026, 7, 15), date(2026, 7, 10))
        self.assertEqual(alerte.niveau, NiveauAlerte.ATTENTION)

    def test_echeance_depassee_alerte_urgente(self):
        alerte = alerte_tva_a_payer(Decimal("500"), date(2026, 7, 1), date(2026, 7, 10))
        self.assertEqual(alerte.niveau, NiveauAlerte.URGENT)


class TestAlerteExercice(unittest.TestCase):
    def test_exercice_non_en_cours_aucune_alerte(self):
        self.assertIsNone(alerte_exercice_proche_cloture(date(2026, 7, 20), date(2026, 7, 10), "cloture"))

    def test_exercice_proche_fin_alerte_info(self):
        alerte = alerte_exercice_proche_cloture(date(2026, 7, 20), date(2026, 7, 10), "en_cours")
        self.assertEqual(alerte.niveau, NiveauAlerte.INFO)

    def test_exercice_loin_de_la_fin_aucune_alerte(self):
        self.assertIsNone(alerte_exercice_proche_cloture(date(2026, 12, 31), date(2026, 7, 10), "en_cours"))


class TestPrioriserAlertes(unittest.TestCase):
    def test_urgent_avant_attention_avant_info(self):
        alertes = [
            alerte_exercice_proche_cloture(date(2026, 7, 20), date(2026, 7, 10), "en_cours"),  # info
            alerte_anomalies(10),  # urgent
            alerte_tva_a_payer(Decimal("500"), date(2026, 7, 15), date(2026, 7, 10)),  # attention
        ]
        resultat = prioriser_alertes(alertes)
        self.assertEqual([a.niveau for a in resultat], [NiveauAlerte.URGENT, NiveauAlerte.ATTENTION, NiveauAlerte.INFO])

    def test_none_filtres(self):
        resultat = prioriser_alertes([None, alerte_anomalies(1), None])
        self.assertEqual(len(resultat), 1)


if __name__ == "__main__":
    unittest.main()
