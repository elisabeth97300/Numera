import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HabitudeComptable(Base):
    """
    Une ligne = 'pour ce client, ce tiers normalisé a été confirmé N fois sur
    ce compte PCG'. Alimentée à chaque validation d'une proposition IA
    (cf. proposition_service.valider), consultée à chaque nouvelle
    proposition pour booster ou contredire la suggestion du LLM.
    """

    __tablename__ = "habitudes_comptables"
    __table_args__ = (UniqueConstraint("client_id", "tiers_normalise", "compte_pcg", name="uq_habitude"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients_dossiers.id"), nullable=False, index=True
    )
    tiers_normalise: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    compte_pcg: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre_confirmations: Mapped[int] = mapped_column(Integer, default=1)
    derniere_confirmation: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
