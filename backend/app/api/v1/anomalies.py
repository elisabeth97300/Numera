from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.services import anomaly_service

router = APIRouter(prefix="/clients/{client_id}/anomalies", tags=["anomalies"])


@router.get("")
def lister_anomalies(
    client_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    anomalies = anomaly_service.detecter_anomalies_client(db, client_id)
    return [
        {
            "type": a.type.value,
            "message": a.message,
            "ecriture_id_1": a.ecriture_id_1,
            "ecriture_id_2": a.ecriture_id_2,
        }
        for a in anomalies
    ]
