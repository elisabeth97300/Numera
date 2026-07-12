from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.schemas.assistant import QuestionAssistant, ReponseAssistant
from app.services import assistant_service, pilotage_service

router = APIRouter(prefix="/clients/{client_id}", tags=["assistant"])


@router.post("/assistant/ask", response_model=ReponseAssistant)
def poser_question(
    client_id: UUID,
    exercice_id: UUID,
    payload: QuestionAssistant,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        reponse = assistant_service.poser_question(db, client_id, exercice_id, payload.question)
    except assistant_service.AssistantError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    return {"reponse": reponse}


@router.get("/alertes")
def lister_alertes(
    client_id: UUID,
    exercice_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alertes = pilotage_service.obtenir_alertes(db, client_id, exercice_id)
    return [{"niveau": a.niveau.value, "message": a.message} for a in alertes]
