import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StatutLigneReleve(str, enum.Enum):
    RAPPROCHE_AUTOMATIQUE = "rapproche_automatique"
    RAPPROCHE_MANUEL = "rapproche_manuel"
    A_VERIFIER = "a_verifier"
    NON_RAPPROCHE = "non_rapproche"


class LigneReleveBancaire(Base):
    __tablename__ = "lignes_releve_bancaire"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients_dossiers.id"), nullable=False, index=True
    )
    document_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents_sources.id"), nullable=True
    )
    date_operation: Mapped[date] = mapped_column(Date, nullable=False)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    statut: Mapped[StatutLigneReleve] = mapped_column(
        Enum(StatutLigneReleve, name="statut_ligne_releve"), default=StatutLigneReleve.NON_RAPPROCHE
    )
    ligne_ecriture_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lignes_ecritures.id"), nullable=True
    )
    code_lettrage: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
