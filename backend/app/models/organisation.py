"""
Modèles Organisation & Utilisateur — squelette de l'étape 1 du plan MVP
(Auth + modèles de base). À enrichir avec les migrations Alembic et la logique
complète d'inscription/permissions quand cette étape sera codée en détail.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoleUtilisateur(str, enum.Enum):
    ADMIN = "admin"
    COMPTABLE = "comptable"
    ASSISTANT = "assistant"


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    siren: Mapped[str | None] = mapped_column(String(9), nullable=True)
    plan_abonnement: Mapped[str] = mapped_column(String(50), default="essai")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    utilisateurs: Mapped[list["Utilisateur"]] = relationship(back_populates="organisation")


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleUtilisateur] = mapped_column(Enum(RoleUtilisateur, name="role_utilisateur"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    organisation: Mapped["Organisation"] = relationship(back_populates="utilisateurs")
