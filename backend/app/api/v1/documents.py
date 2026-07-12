from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.domain.document_domain import DocumentError
from app.schemas.document import DocumentOut, DocumentUploadResponse
from app.services import document_service

router = APIRouter(tags=["documents"])


@router.post(
    "/clients/{client_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED
)
async def importer_document(
    client_id: UUID,
    type_document: str,
    fichier: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contenu = await fichier.read()
    try:
        document, doublon = document_service.importer_document(
            db, client_id, fichier.filename, contenu, type_document
        )
    except DocumentError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return {
        "document": document,
        "doublon_detecte": doublon is not None,
        "document_doublon_id": doublon.id if doublon else None,
    }


@router.get("/documents/{document_id}", response_model=DocumentOut)
def obtenir_document(
    document_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = document_service.obtenir_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")
    return document
