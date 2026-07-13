from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.document_domain import (
    DocumentError,
    TypeDocument as TypeDocumentDomain,
    calculer_hash,
    valider_fichier,
)
from app.models.client import ClientDossier
from app.models.document import DocumentSource, StatutOCR
from app.schemas.document import DocumentOut, DocumentUploadResponse
from app.services import document_service

router = APIRouter(tags=["documents"])

DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_UPLOAD_DIR = Path("/tmp/numera-demo-uploads")


@router.post(
    "/clients/{client_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def importer_document(
    client_id: UUID,
    type_document: str,
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Route temporaire de démonstration.

    Elle autorise uniquement le client démo, stocke le fichier dans /tmp
    et n'exige pas d'authentification.
    """
    if client_id != DEMO_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le dossier de démonstration est autorisé.",
        )

    client = db.get(ClientDossier, client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier de démonstration introuvable.",
        )

    contenu = await fichier.read()

    try:
        type_enum = TypeDocumentDomain(type_document)
        valider_fichier(
            fichier.filename or "document.bin",
            len(contenu),
            type_enum,
        )
    except (DocumentError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    DEMO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    nom_fichier = fichier.filename or "document.bin"
    chemin = DEMO_UPLOAD_DIR / f"{uuid4()}-{nom_fichier}"
    chemin.write_bytes(contenu)

    document = DocumentSource(
        client_id=client_id,
        type_document=type_document,
        fichier_s3_url=str(chemin),
        statut_ocr=StatutOCR.EN_ATTENTE,
        hash_fichier=calculer_hash(contenu),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "document": document,
        "doublon_detecte": False,
        "document_doublon_id": None,
    }


@router.get("/documents/{document_id}", response_model=DocumentOut)
def obtenir_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    document = document_service.obtenir_document(db, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document introuvable",
        )
    return document
