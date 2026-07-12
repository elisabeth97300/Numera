"""
Modèle ClientDossier — le dossier d'une entreprise cliente gérée par le cabinet.
Squelette minimal ; à enrichir (régime de TVA, plan comptable, etc. déjà prévus
dans le document d'architecture) quand cette étape sera développée en détail.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RegimeTVA(str, enum.Enum):
    REEL_NORMAL = "reel_normal"
    REEL_SIMPLIFIE = "reel_simplifie"
    FRANCHISE = "franchise"


class ClientDossier(Base):
    __tablename__ = "clients_dossiers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False, index=True
    )
    raison_sociale: Mapped[str] = mapped_column(String(200), nullable=False)
    siren: Mapped[str | None] = mapped_column(String(9), nullable=True)
    regime_tva: Mapped[RegimeTVA] = mapped_column(Enum(RegimeTVA, name="regime_tva"), default=RegimeTVA.REEL_NORMAL)
    plan_comptable: Mapped[str] = mapped_column(String(20), default="PCG-2014")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
