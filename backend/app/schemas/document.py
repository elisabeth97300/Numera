from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: UUID
    client_id: UUID
    type_document: str
    statut_ocr: str
    donnees_extraites: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentOut
    doublon_detecte: bool = False
    document_doublon_id: UUID | None = None
