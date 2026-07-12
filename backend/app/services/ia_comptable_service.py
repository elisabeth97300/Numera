"""
Service IA Comptable : transforme le résultat OCR d'un document en
proposition d'écriture structurée, via un appel à l'API Anthropic.

Le prompt force une réponse JSON stricte (aucun texte autour) pour que le
parsing soit fiable. Le résultat brut du LLM passe ensuite systématiquement
par app/domain/proposition_domain.valider_proposition avant d'être persisté
— cette fonction ne fait confiance à rien de ce que le LLM répond sans
validation, y compris le format du compte PCG.

NOTE : nécessite une clé API valide dans LLM_API_KEY. Ce module n'a pas pu
être exécuté dans l'environnement de génération de ce code (pas de réseau
dans ce sandbox) ; à tester avec une vraie clé avant mise en production.
"""

import json
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import get_settings
from app.domain.proposition_domain import PropositionBrute, PropositionError

settings = get_settings()

PROMPT_SYSTEME = """Tu es un assistant qui prépare des écritures comptables en France.
On te donne le texte brut extrait par OCR d'un document (facture d'achat en général).
Réponds UNIQUEMENT avec un objet JSON, sans aucun texte avant ou après, au format exact :
{
  "compte_pcg": "code à 6 chiffres du Plan Comptable Général français, ex: 606100",
  "tiers": "nom du fournisseur",
  "montant_ht": nombre décimal,
  "montant_tva": nombre décimal,
  "taux_tva": nombre décimal (ex: 20, 10, 5.5, 2.1, ou 0),
  "score_confiance": nombre décimal entre 0 et 1 représentant ta confiance dans cette lecture
}
Si une information est illisible ou absente, mets un score_confiance bas plutôt que d'inventer une valeur.
"""


class IAComptableError(Exception):
    """Erreur lors de l'appel au LLM ou du parsing de sa réponse."""


def _appeler_llm(texte_ocr: str) -> dict:
    if not settings.llm_api_key:
        raise IAComptableError("LLM_API_KEY non configurée")

    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.llm_model,
            "max_tokens": 500,
            "system": PROMPT_SYSTEME,
            "messages": [{"role": "user", "content": texte_ocr}],
        },
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()

    texte_reponse = "".join(bloc["text"] for bloc in data["content"] if bloc["type"] == "text")
    texte_reponse = texte_reponse.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(texte_reponse)
    except json.JSONDecodeError as e:
        raise IAComptableError(f"Réponse du LLM non exploitable : {e}") from e


def generer_proposition_brute(texte_ocr: str) -> PropositionBrute:
    """Appelle le LLM et convertit sa réponse JSON en PropositionBrute (pas encore validée métier)."""
    brut = _appeler_llm(texte_ocr)

    champs_requis = {"compte_pcg", "tiers", "montant_ht", "montant_tva", "taux_tva", "score_confiance"}
    manquants = champs_requis - brut.keys()
    if manquants:
        raise IAComptableError(f"Champs manquants dans la réponse du LLM : {manquants}")

    try:
        return PropositionBrute(
            compte_pcg=str(brut["compte_pcg"]),
            tiers=str(brut["tiers"]),
            montant_ht=Decimal(str(brut["montant_ht"])),
            montant_tva=Decimal(str(brut["montant_tva"])),
            taux_tva=Decimal(str(brut["taux_tva"])),
            score_confiance=float(brut["score_confiance"]),
        )
    except (InvalidOperation, ValueError, TypeError) as e:
        raise PropositionError(f"Valeurs renvoyées par le LLM invalides : {e}") from e
