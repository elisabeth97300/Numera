from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.services import graph_service

router = APIRouter(prefix="/clients/{client_id}/graphe", tags=["graphe"])


@router.get("")
def obtenir_graphe(
    client_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return graph_service.construire_graphe_client(db, client_id)
