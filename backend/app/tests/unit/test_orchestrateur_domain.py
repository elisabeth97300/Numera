import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.orchestrateur_domain import NomAgent, router_question  # noqa: E402


class TestRouterQuestion(unittest.TestCase):
    def test_question_tresorerie(self):
        self.assertEqual(router_question("Quelle est ma trésorerie prévue dans 90 jours ?").agent, NomAgent.AGENT_TRESORERIE)

    def test_question_analyse_resultat(self):
        self.assertEqual(router_question("Pourquoi mon bénéfice baisse ?").agent, NomAgent.AGENT_ANALYSE)

    def test_question_embauche_route_vers_analyse(self):
        self.assertEqual(router_question("Puis-je embaucher un salarié ?").agent, NomAgent.AGENT_ANALYSE)

    def test_question_depenses(self):
        self.assertEqual(router_question("Quelles dépenses puis-je réduire ?").agent, NomAgent.AGENT_DEPENSES)

    def test_question_banque(self):
        self.assertEqual(router_question("Peux-tu vérifier mon relevé bancaire ?").agent, NomAgent.AGENT_BANQUE)

    def test_question_tva(self):
        self.assertEqual(router_question("Combien de TVA dois-je payer ce mois-ci ?").agent, NomAgent.AGENT_TVA)

    def test_question_anomalies(self):
        self.assertEqual(router_question("Y a-t-il des doublons dans mes écritures ?").agent, NomAgent.AGENT_AUDIT)

    def test_question_hors_perimetre_route_vers_generaliste(self):
        self.assertEqual(router_question("Quel temps fait-il ?").agent, NomAgent.AGENT_GENERALISTE)

    def test_score_reflete_nombre_de_correspondances(self):
        decision = router_question("Ma trésorerie et mon solde de liquidité sont-ils sains ?")
        self.assertEqual(decision.agent, NomAgent.AGENT_TRESORERIE)
        self.assertGreaterEqual(decision.score, 2)


if __name__ == "__main__":
    unittest.main()
