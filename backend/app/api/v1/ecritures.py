from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.domain.exercice_domain import ExerciceError
from app.services import ecriture_service

router = APIRouter(prefix="/clients/{client_id}/ecritures", tags=["ecritures"])
router_global = APIRouter(prefix="/ecritures", tags=["ecritures"])


@router.get("")
def lister_ecritures(
    client_id: UUID,
    journal: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ecritures = ecriture_service.lister_ecritures(db, client_id, journal)
    return [
        {
            "id": e.id,
            "journal": e.journal.value,
            "date_ecriture": e.date_ecriture,
            "libelle": e.libelle,
            "statut": e.statut.value,
            "lignes": [
                {"compte_pcg": l.compte_pcg, "libelle": l.libelle, "debit": l.debit, "credit": l.credit}
                for l in e.lignes
            ],
        }
        for e in ecritures
    ]


@router_global.post("/{ecriture_id}/extourner")
def extourner_ecriture(
    ecriture_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        extourne = ecriture_service.extourner_ecriture(db, ecriture_id, current_user.id)
    except ExerciceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"id": extourne.id, "libelle": extourne.libelle}
