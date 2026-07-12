"""
Orchestrateur multi-agents : route une question en langage naturel vers
l'agent spécialisé le plus pertinent (Agent Trésorerie, Agent Analyse/CFO,
Agent Banque, Agent Comptable, Agent Audit...).

Deux mécanismes possibles pour router :
1. Un classement par mots-clés, déterministe et testable — implémenté ici,
   sert de première ligne et de repli si le LLM est indisponible.
2. Une classification par le LLM lui-même (tool-calling), plus flexible mais
   non testable en environnement sans réseau — c'est ce que fait
   assistant_service.py en pratique : le modèle "choisit" son outil, ce qui
   revient à un routage géré par le LLM plutôt que par ce module.

Ce module reste utile comme repli déterministe et comme brique de test de la
logique de routage indépendamment du LLM.
"""

from dataclasses import dataclass
from enum import Enum


class NomAgent(str, Enum):
    AGENT_TRESORERIE = "agent_tresorerie"
    AGENT_ANALYSE = "agent_analyse"  # synthèse "CFO" : comparaisons, rentabilité, recommandations
    AGENT_DEPENSES = "agent_depenses"
    AGENT_BANQUE = "agent_banque"
    AGENT_TVA = "agent_tva"
    AGENT_AUDIT = "agent_audit"  # anomalies, contrôle
    AGENT_GENERALISTE = "agent_generaliste"  # repli si aucune correspondance claire


MOTS_CLES_PAR_AGENT: dict[NomAgent, list[str]] = {
    NomAgent.AGENT_TRESORERIE: ["trésorerie", "tresorerie", "solde", "cash", "liquidité", "liquidite"],
    NomAgent.AGENT_ANALYSE: ["bénéfice", "benefice", "marge", "rentabilité", "rentabilite", "résultat", "resultat", "chiffre d'affaires", "embaucher", "embauche", "investir", "investissement"],
    NomAgent.AGENT_DEPENSES: ["dépense", "depense", "coût", "cout", "réduire", "reduire", "économiser", "economiser"],
    NomAgent.AGENT_BANQUE: ["banque", "relevé", "releve", "rapprochement", "virement", "prélèvement", "prelevement"],
    NomAgent.AGENT_TVA: ["tva", "déclaration", "declaration", "impôt", "impot", "fiscal"],
    NomAgent.AGENT_AUDIT: ["anomalie", "erreur", "doublon", "incohérence", "incoherence", "contrôle", "controle"],
}


@dataclass
class DecisionRoutage:
    agent: NomAgent
    score: int  # nombre de mots-clés correspondants ; utile pour debug/observabilité


def router_question(question: str) -> DecisionRoutage:
    """
    Compte les correspondances de mots-clés par agent et retient le meilleur
    score. En cas d'égalité, l'ordre de MOTS_CLES_PAR_AGENT fait foi (le
    premier agent testé gagne) — déterministe, donc testable.
    """
    q = question.lower()
    meilleur_agent = NomAgent.AGENT_GENERALISTE
    meilleur_score = 0

    for agent, mots_cles in MOTS_CLES_PAR_AGENT.items():
        score = sum(1 for mot in mots_cles if mot in q)
        if score > meilleur_score:
            meilleur_score = score
            meilleur_agent = agent

    return DecisionRoutage(agent=meilleur_agent, score=meilleur_score)
