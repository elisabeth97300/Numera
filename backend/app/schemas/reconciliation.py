from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class LigneReleveOut(BaseModel):
    id: UUID
    date_operation: date
    libelle: str
    montant: Decimal
    statut: str
    ligne_ecriture_id: UUID | None = None
    code_lettrage: str | None = None
    candidats_alternatifs: list[UUID] = []

    model_config = {"from_attributes": True}


class ImportReleveResponse(BaseModel):
    lignes: list[LigneReleveOut]
    nombre_rapprochees: int
    nombre_a_verifier: int
    nombre_non_rapprochees: int
    taux_rapprochement: float


class ValiderLettrageRequest(BaseModel):
    ligne_ecriture_id: UUID
