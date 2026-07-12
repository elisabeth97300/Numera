import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StatutProposition(str, enum.Enum):
    EN_ATTENTE = "en_attente"
    VALIDEE = "validee"
    MODIFIEE = "modifiee"
    REJETEE = "rejetee"


class PropositionIA(Base):
    __tablename__ = "propositions_ia"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents_sources.id"), nullable=False, index=True
    )
    compte_propose: Mapped[str] = mapped_column(String(20), nullable=False)
    tiers_propose: Mapped[str] = mapped_column(String(200), nullable=False)
    montant_ht: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    montant_tva: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    taux_tva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_confiance: Mapped[float] = mapped_column(Float, nullable=False)
    a_verifier_en_priorite: Mapped[bool] = mapped_column(Boolean, default=False)
    avertissements: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    statut: Mapped[StatutProposition] = mapped_column(
        Enum(StatutProposition, name="statut_proposition"), default=StatutProposition.EN_ATTENTE
    )
    modele_ia_version: Mapped[str] = mapped_column(String(50), default="claude-sonnet-4-6")
    ecriture_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ecritures.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
