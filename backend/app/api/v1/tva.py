from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.services import tva_service

router = APIRouter(prefix="/clients/{client_id}/tva", tags=["tva"])


@router.get("/preparation")
def preparation_tva(
    client_id: UUID,
    exercice_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prep = tva_service.obtenir_preparation_tva(db, exercice_id)
    return {
        "collectee_par_taux": [
            {"taux": v.taux, "base_ht": v.base_ht, "montant_tva": v.montant_tva} for v in prep.collectee_par_taux
        ],
        "deductible_par_taux": [
            {"taux": v.taux, "base_ht": v.base_ht, "montant_tva": v.montant_tva} for v in prep.deductible_par_taux
        ],
        "total_collectee": prep.total_collectee(),
        "total_deductible": prep.total_deductible(),
        "solde_a_payer": prep.solde_a_payer(),
    }
