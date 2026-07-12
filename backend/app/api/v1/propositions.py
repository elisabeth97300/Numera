from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.domain.exercice_domain import ExerciceError
from app.schemas.proposition import PropositionModification, PropositionOut
from app.services import proposition_service

router = APIRouter(tags=["propositions"])


@router.get("/clients/{client_id}/propositions", response_model=list[PropositionOut])
def lister_propositions(
    client_id: UUID,
    statut: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return proposition_service.lister_propositions(db, client_id, statut)


@router.post("/propositions/{proposition_id}/valider", response_model=PropositionOut)
def valider_proposition(
    proposition_id: UUID,
    exercice_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return proposition_service.valider(db, proposition_id, exercice_id, current_user.id)
    except ExerciceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/propositions/{proposition_id}/modifier", response_model=PropositionOut)
def modifier_proposition(
    proposition_id: UUID,
    payload: PropositionModification,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return proposition_service.modifier(db, proposition_id, payload.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/propositions/{proposition_id}/rejeter", response_model=PropositionOut)
def rejeter_proposition(
    proposition_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return proposition_service.rejeter(db, proposition_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
