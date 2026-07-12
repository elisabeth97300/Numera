"""
Schémas Pydantic pour l'API des exercices comptables (validation des requêtes
et des réponses HTTP). Ces schémas sont volontairement séparés des modèles
SQLAlchemy (app/models/exercice.py) : l'API n'expose jamais un modèle de base
de données directement.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OrigineExerciceSchema(str, Enum):
    NOUVEAU = "nouveau"
    REPRIS = "repris"


class StatutExerciceSchema(str, Enum):
    NON_DEMARRE = "non_demarre"
    EN_COURS = "en_cours"
    CLOTURE = "cloture"
    ARCHIVE = "archive"


class LigneSoldeIn(BaseModel):
    """Une ligne saisie manuellement par le comptable pour le bilan d'ouverture."""

    compte_pcg: str = Field(..., min_length=3, max_length=20, examples=["512000"])
    solde_debit: Decimal = Field(default=Decimal("0"), ge=0)
    solde_credit: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("compte_pcg")
    @classmethod
    def compte_doit_commencer_par_un_chiffre(cls, v: str) -> str:
        if not v[0].isdigit():
            raise ValueError("Un compte PCG doit commencer par un chiffre (classe comptable)")
        return v


class LigneSoldeOut(LigneSoldeIn):
    id: UUID
    source: str


class ExerciceCreate(BaseModel):
    """Requête de création d'un exercice comptable."""

    date_debut: date
    date_fin: date
    origine: OrigineExerciceSchema
    exercice_precedent_id: Optional[UUID] = None

    @field_validator("date_fin")
    @classmethod
    def fin_apres_debut(cls, v: date, info) -> date:
        debut = info.data.get("date_debut")
        if debut and v <= debut:
            raise ValueError("La date de fin doit être postérieure à la date de début")
        return v


class SoldeOuvertureSaisieManuelle(BaseModel):
    """
    Corps de la requête `POST /exercices/{id}/solde-ouverture` : le comptable
    saisit le bilan de clôture de l'exercice antérieur, compte par compte.
    """

    lignes: list[LigneSoldeIn] = Field(..., min_length=1)


class ExerciceOut(BaseModel):
    id: UUID
    client_id: UUID
    date_debut: date
    date_fin: date
    statut: StatutExerciceSchema
    origine: OrigineExerciceSchema
    date_cloture: Optional[datetime] = None
    exercice_precedent_id: Optional[UUID] = None
    soldes_ouverture: list[LigneSoldeOut] = []

    model_config = {"from_attributes": True}


class ClotureExerciceResponse(BaseModel):
    exercice: ExerciceOut
    exercice_suivant_cree: Optional[UUID] = None
    nombre_lignes_solde_reporte: int
