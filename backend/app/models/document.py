import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TypeDocument(str, enum.Enum):
    FACTURE_ACHAT = "facture_achat"
    FACTURE_VENTE = "facture_vente"
    RELEVE_BANCAIRE = "releve_bancaire"
    FEC = "fec"
    AUTRE = "autre"


class StatutOCR(str, enum.Enum):
    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ERREUR = "erreur"


class DocumentSource(Base):
    __tablename__ = "documents_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients_dossiers.id"), nullable=False, index=True
    )
    type_document: Mapped[TypeDocument] = mapped_column(Enum(TypeDocument, name="type_document"), nullable=False)
    fichier_s3_url: Mapped[str] = mapped_column(String(500), nullable=False)
    statut_ocr: Mapped[StatutOCR] = mapped_column(
        Enum(StatutOCR, name="statut_ocr"), default=StatutOCR.EN_ATTENTE
    )
    donnees_extraites: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    hash_fichier: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
