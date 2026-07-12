from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.domain.auth_domain import AutorisationError
from app.schemas.client import ClientCreate, ClientOut
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def lister_clients(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return client_service.lister_clients(db, current_user.organisation_id)


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def creer_client(
    payload: ClientCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return client_service.creer_client(db, current_user.organisation_id, payload.model_dump())


@router.get("/{client_id}", response_model=ClientOut)
def obtenir_client(
    client_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        client = client_service.obtenir_client(db, client_id, current_user.organisation_id)
    except AutorisationError as e:
        # 404 plutôt que 403 : on ne révèle même pas qu'une ressource d'une
        # autre organisation existe à cet identifiant.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return client
