import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # backend/

from app.domain.prevision_domain import (  # noqa: E402
    PrevisionError,
    estimer_is,
    prevoir_prochaine_tva,
    simuler_charge_recurrente,
    simuler_investissement_ponctuel,
)
from app.domain.tresorerie_domain import MouvementJournalier, projeter_tresorerie  # noqa: E402


class TestPrevoirProchaineTVA(unittest.TestCase):
    def test_moyenne_simple(self):
        self.assertEqual(prevoir_prochaine_tva([Decimal("1000"), Decimal("2000"), Decimal("1500")]), Decimal("1500"))

    def test_historique_vide_leve_erreur(self):
        with self.assertRaises(PrevisionError):
            prevoir_prochaine_tva([])


class TestEstimerIS(unittest.TestCase):
    def test_resultat_negatif_is_nul(self):
        self.assertEqual(estimer_is(Decimal("-1000")), Decimal("0"))

    def test_sous_le_seuil_taux_reduit(self):
        self.assertEqual(estimer_is(Decimal("20000")), Decimal("3000"))  # 15%

    def test_au_dessus_du_seuil_deux_tranches(self):
        resultat = estimer_is(Decimal("50000"))
        attendu = Decimal("42500") * Decimal("0.15") + Decimal("7500") * Decimal("0.25")
        self.assertEqual(resultat, attendu)

    def test_non_eligible_taux_reduit_taux_normal_partout(self):
        resultat = estimer_is(Decimal("20000"), eligible_taux_reduit=False)
        self.assertEqual(resultat, Decimal("5000"))  # 25%


class TestSimulerChargeRecurrente(unittest.TestCase):
    def test_charge_supplementaire_degrade_la_projection(self):
        mouvements = [MouvementJournalier(date(2026, 7, i), Decimal("100")) for i in range(1, 11)]
        base = projeter_tresorerie(Decimal("5000"), mouvements, horizon_jours=90)
        simulee = simuler_charge_recurrente(base, mouvements, cout_mensuel=Decimal("3000"))
        self.assertLess(simulee.solde_projete, base.solde_projete)

    def test_horizon_et_solde_actuel_inchanges(self):
        mouvements = [MouvementJournalier(date(2026, 7, 1), Decimal("100"))]
        base = projeter_tresorerie(Decimal("5000"), mouvements, horizon_jours=60)
        simulee = simuler_charge_recurrente(base, mouvements, cout_mensuel=Decimal("1000"))
        self.assertEqual(simulee.horizon_jours, 60)
        self.assertEqual(simulee.solde_actuel, Decimal("5000"))


class TestSimulerInvestissementPonctuel(unittest.TestCase):
    def test_investissement_reduit_tous_les_scenarios_du_meme_montant(self):
        mouvements = [MouvementJournalier(date(2026, 7, 1), Decimal("100"))]
        base = projeter_tresorerie(Decimal("10000"), mouvements, horizon_jours=90)
        simulee = simuler_investissement_ponctuel(base, Decimal("4000"))
        self.assertEqual(simulee.solde_actuel, base.solde_actuel - Decimal("4000"))
        self.assertEqual(simulee.solde_projete, base.solde_projete - Decimal("4000"))
        self.assertEqual(simulee.scenario_pessimiste, base.scenario_pessimiste - Decimal("4000"))

    def test_montant_negatif_refuse(self):
        mouvements = [MouvementJournalier(date(2026, 7, 1), Decimal("100"))]
        base = projeter_tresorerie(Decimal("10000"), mouvements, horizon_jours=90)
        with self.assertRaises(PrevisionError):
            simuler_investissement_ponctuel(base, Decimal("-100"))


if __name__ == "__main__":
    unittest.main()
