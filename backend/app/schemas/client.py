from uuid import UUID

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    raison_sociale: str = Field(..., min_length=2, max_length=200)
    siren: str | None = Field(None, min_length=9, max_length=9)
    regime_tva: str = Field(default="reel_normal", pattern="^(reel_normal|reel_simplifie|franchise)$")
    plan_comptable: str = "PCG-2014"


class ClientOut(BaseModel):
    id: UUID
    organisation_id: UUID
    raison_sociale: str
    siren: str | None
    regime_tva: str
    plan_comptable: str

    model_config = {"from_attributes": True}
