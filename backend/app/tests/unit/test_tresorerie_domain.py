import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.tresorerie_domain import (  # noqa: E402
    MouvementJournalier,
    TresorerieError,
    projeter_tresorerie,
)


class TestProjeterTresorerie(unittest.TestCase):
    def test_projection_simple_avec_mouvement_constant(self):
        mouvements = [MouvementJournalier(date(2026, 7, i), Decimal("100")) for i in range(1, 11)]
        projection = projeter_tresorerie(Decimal("5000"), mouvements, horizon_jours=90)
        self.assertEqual(projection.moyenne_mouvement_journalier, Decimal("100"))
        self.assertEqual(projection.solde_projete, Decimal("5000") + Decimal("100") * 90)

    def test_scenario_pessimiste_utilise_la_pire_journee(self):
        mouvements = [
            MouvementJournalier(date(2026, 7, 1), Decimal("200")),
            MouvementJournalier(date(2026, 7, 2), Decimal("-500")),
            MouvementJournalier(date(2026, 7, 3), Decimal("100")),
        ]
        projection = projeter_tresorerie(Decimal("1000"), mouvements, horizon_jours=30)
        self.assertEqual(projection.scenario_pessimiste, Decimal("1000") + Decimal("-500") * 30)

    def test_risque_decouvert_detecte(self):
        mouvements = [MouvementJournalier(date(2026, 7, 1), Decimal("-1000"))]
        projection = projeter_tresorerie(Decimal("500"), mouvements, horizon_jours=10)
        self.assertTrue(projection.risque_decouvert())

    def test_pas_de_risque_si_tous_scenarios_positifs(self):
        mouvements = [MouvementJournalier(date(2026, 7, 1), Decimal("500"))]
        projection = projeter_tresorerie(Decimal("10000"), mouvements, horizon_jours=10)
        self.assertFalse(projection.risque_decouvert())

    def test_aucun_historique_leve_une_erreur(self):
        with self.assertRaises(TresorerieError):
            projeter_tresorerie(Decimal("1000"), [], horizon_jours=90)

    def test_horizon_negatif_leve_une_erreur(self):
        mouvements = [MouvementJournalier(date(2026, 7, 1), Decimal("100"))]
        with self.assertRaises(TresorerieError):
            projeter_tresorerie(Decimal("1000"), mouvements, horizon_jours=-5)


if __name__ == "__main__":
    unittest.main()
