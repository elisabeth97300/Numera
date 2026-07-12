"""
Orchestrateur de l'assistant conversationnel.

1. Route la question vers l'agent spécialisé pertinent
   (app/domain/orchestrateur_domain.router_question).
2. Utilise le system prompt et le sous-ensemble d'outils de cet agent
   (app/services/agents/definitions.py).
3. Pilote la boucle d'appels d'outils avec l'API Anthropic (tool use) : le
   LLM ne répond jamais de tête sur un chiffre, il doit appeler un outil qui
   va chercher la vraie donnée via app/services/pilotage_service.py.

NOTE : comme ia_comptable_service.py, ce module nécessite une clé API valide
(LLM_API_KEY) et n'a pas pu être exécuté dans ce sandbox sans réseau. Le
routage vers l'agent (étape 1) est en revanche pur et testé indépendamment
dans app/tests/unit/test_orchestrateur_domain.py.
"""

import json
from decimal import Decimal
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.orchestrateur_domain import router_question
from app.services import pilotage_service
from app.services.agents.definitions import AGENTS

settings = get_settings()

DEFINITIONS_OUTILS = {
    "projection_tresorerie": {
        "name": "projection_tresorerie",
        "description": "Projette le solde de trésorerie à un horizon donné, avec un scénario optimiste et pessimiste.",
        "input_schema": {
            "type": "object",
            "properties": {"horizon_jours": {"type": "integer", "description": "Nombre de jours à projeter, ex: 90"}},
            "required": ["horizon_jours"],
        },
    },
    "rentabilite_clients": {
        "name": "rentabilite_clients",
        "description": "Classe les clients du moins au plus rentable sur l'exercice en cours.",
        "input_schema": {"type": "object", "properties": {}},
    },
    "comparaison_resultat": {
        "name": "comparaison_resultat",
        "description": "Compare le résultat de l'exercice courant à l'exercice précédent et identifie les postes qui expliquent le plus la variation.",
        "input_schema": {"type": "object", "properties": {}},
    },
    "depenses_reductibles": {
        "name": "depenses_reductibles",
        "description": "Identifie les postes de charges discrétionnaires (compressibles) les plus importants.",
        "input_schema": {"type": "object", "properties": {}},
    },
}


class AssistantError(Exception):
    pass


def _serialiser(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialiser(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_serialiser(v) for v in obj]
    return obj


def _executer_outil(db: Session, client_id: UUID, exercice_id: UUID, nom: str, params: dict) -> dict:
    if nom == "projection_tresorerie":
        return _serialiser(
            pilotage_service.obtenir_projection_tresorerie(db, client_id, exercice_id, horizon_jours=params.get("horizon_jours", 90))
        )
    if nom == "rentabilite_clients":
        return {"clients": _serialiser(pilotage_service.obtenir_rentabilite_clients(db, client_id, exercice_id))}
    if nom == "comparaison_resultat":
        resultat = pilotage_service.obtenir_comparaison_resultats(db, exercice_id)
        if resultat is None:
            return {"erreur": "Pas d'exercice précédent disponible pour comparer"}
        return _serialiser(resultat)
    if nom == "depenses_reductibles":
        return {"suggestions": _serialiser(pilotage_service.obtenir_depenses_reductibles(db, exercice_id))}
    raise AssistantError(f"Outil inconnu : {nom}")


def _appeler_llm(system_prompt: str, outils: list[dict], messages: list[dict]) -> dict:
    if not settings.llm_api_key:
        raise AssistantError("LLM_API_KEY non configurée")

    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "max_tokens": 1000,
            "system": system_prompt,
            "tools": outils,
            "messages": messages,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def poser_question(db: Session, client_id: UUID, exercice_id: UUID, question: str, max_tours: int = 4) -> str:
    """
    Point d'entrée de l'orchestrateur : route vers l'agent pertinent, puis
    pilote sa boucle d'outils jusqu'à obtenir une réponse texte finale.
    """
    decision = router_question(question)
    agent = AGENTS[decision.agent]
    outils_agent = [DEFINITIONS_OUTILS[nom] for nom in agent.outils]

    messages = [{"role": "user", "content": question}]

    for _ in range(max_tours):
        reponse = _appeler_llm(agent.prompt_systeme, outils_agent, messages)

        blocs_outils = [b for b in reponse["content"] if b["type"] == "tool_use"]
        blocs_texte = [b["text"] for b in reponse["content"] if b["type"] == "text"]

        if not blocs_outils:
            return "\n".join(blocs_texte) if blocs_texte else "Je n'ai pas de réponse à apporter."

        messages.append({"role": "assistant", "content": reponse["content"]})

        resultats_outils = []
        for bloc in blocs_outils:
            try:
                resultat = _executer_outil(db, client_id, exercice_id, bloc["name"], bloc.get("input", {}))
                contenu = json.dumps(resultat, ensure_ascii=False)
            except Exception as e:  # noqa: BLE001
                contenu = json.dumps({"erreur": str(e)}, ensure_ascii=False)
            resultats_outils.append({"type": "tool_result", "tool_use_id": bloc["id"], "content": contenu})

        messages.append({"role": "user", "content": resultats_outils})

    raise AssistantError("Trop d'allers-retours avec le modèle sans réponse finale")
