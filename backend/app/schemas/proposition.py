from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class PropositionOut(BaseModel):
    id: UUID
    document_source_id: UUID
    compte_propose: str
    tiers_propose: str
    montant_ht: Decimal
    montant_tva: Decimal
    taux_tva: Decimal
    score_confiance: float
    a_verifier_en_priorite: bool
    avertissements: list[str] | None = None
    statut: str

    model_config = {"from_attributes": True}


class PropositionModification(BaseModel):
    """Corrections apportées par le comptable avant validation."""

    compte_propose: str | None = None
    tiers_propose: str | None = None
    montant_ht: Decimal | None = None
    montant_tva: Decimal | None = None
