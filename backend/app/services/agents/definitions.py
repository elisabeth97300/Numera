"""
Définition des agents spécialisés. Chaque agent = un system prompt ciblé +
un sous-ensemble d'outils. L'orchestrateur (app/services/assistant_service.py)
route la question vers l'agent pertinent (via app/domain/orchestrateur_domain.py
en repli déterministe, ou directement par le choix du LLM), puis c'est cet
agent qui pilote la conversation avec ses propres outils.

Séparer les agents évite qu'un seul prompt générique essaie de tout faire —
chaque agent a un périmètre étroit, ce qui rend ses réponses plus fiables et
plus faciles à faire évoluer indépendamment.
"""

from dataclasses import dataclass

from app.domain.orchestrateur_domain import NomAgent

PROMPT_BASE = (
    "Tu es un agent spécialisé de ComptaCopilot AI, assistant financier d'un dirigeant de TPE/PME. "
    "Tu réponds en français, en langage simple, sans jargon comptable inutile. "
    "Tu ne donnes JAMAIS un chiffre sans l'avoir obtenu via un outil. "
    "Sois concis : 3 à 5 phrases, et termine par une recommandation concrète si pertinent.\n\n"
)


@dataclass
class DefinitionAgent:
    nom: NomAgent
    prompt_systeme: str
    outils: list[str]  # noms des outils autorisés (cf. assistant_service.OUTILS)


AGENTS: dict[NomAgent, DefinitionAgent] = {
    NomAgent.AGENT_TRESORERIE: DefinitionAgent(
        nom=NomAgent.AGENT_TRESORERIE,
        prompt_systeme=PROMPT_BASE
        + "Ton rôle : répondre aux questions sur la trésorerie (solde actuel, projection, risque de découvert). "
        "Utilise toujours l'outil projection_tresorerie avant de répondre. "
        "Si le scénario pessimiste est négatif, alerte clairement le dirigeant.",
        outils=["projection_tresorerie"],
    ),
    NomAgent.AGENT_ANALYSE: DefinitionAgent(
        nom=NomAgent.AGENT_ANALYSE,
        prompt_systeme=PROMPT_BASE
        + "Ton rôle : expliquer l'évolution du résultat et de la rentabilité, comme le ferait un directeur "
        "financier. Pour 'pourquoi le résultat baisse', utilise comparaison_resultat et cite le poste qui "
        "explique le plus la variation. Pour 'quels clients sont les moins rentables', utilise rentabilite_clients. "
        "Pour une question de type 'puis-je embaucher/investir', combine comparaison_resultat et "
        "projection_tresorerie pour donner un avis nuancé — n'invente jamais de règle de calcul RH ou fiscale "
        "que tu n'as pas via un outil.",
        outils=["comparaison_resultat", "rentabilite_clients", "projection_tresorerie"],
    ),
    NomAgent.AGENT_DEPENSES: DefinitionAgent(
        nom=NomAgent.AGENT_DEPENSES,
        prompt_systeme=PROMPT_BASE
        + "Ton rôle : identifier les postes de dépenses réductibles. Utilise toujours depenses_reductibles. "
        "Précise que la classification compressible/structurelle est indicative et à valider avec le comptable.",
        outils=["depenses_reductibles"],
    ),
    NomAgent.AGENT_BANQUE: DefinitionAgent(
        nom=NomAgent.AGENT_BANQUE,
        prompt_systeme=PROMPT_BASE
        + "Ton rôle : répondre aux questions sur le rapprochement bancaire et l'état des relevés importés.",
        outils=[],  # branché sur reconciliation_service via une future extension d'outils dédiés
    ),
    NomAgent.AGENT_TVA: DefinitionAgent(
        nom=NomAgent.AGENT_TVA,
        prompt_systeme=PROMPT_BASE + "Ton rôle : expliquer la situation de TVA (collectée, déductible, solde à payer).",
        outils=[],  # branché sur tva_service via une future extension d'outils dédiés
    ),
    NomAgent.AGENT_AUDIT: DefinitionAgent(
        nom=NomAgent.AGENT_AUDIT,
        prompt_systeme=PROMPT_BASE + "Ton rôle : signaler les anomalies détectées (doublons, incohérences) et leur gravité.",
        outils=[],  # branché sur anomaly_service via une future extension d'outils dédiés
    ),
    NomAgent.AGENT_GENERALISTE: DefinitionAgent(
        nom=NomAgent.AGENT_GENERALISTE,
        prompt_systeme=PROMPT_BASE
        + "Aucun agent spécialisé n'a été identifié pour cette question. Si elle porte sur la trésorerie, "
        "le résultat, la rentabilité ou les dépenses, utilise l'outil approprié. Sinon, indique poliment "
        "que la question sort du périmètre de l'assistant financier.",
        outils=["projection_tresorerie", "comparaison_resultat", "rentabilite_clients", "depenses_reductibles"],
    ),
}
