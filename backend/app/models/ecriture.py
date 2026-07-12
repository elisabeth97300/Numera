"""
Modèles Ecriture & LigneEcriture — squelette de l'étape 5 du plan MVP (partie
double + contrôle d'équilibre). Volontairement minimal ici : le service
exercice_service.py s'appuie sur cette structure (Ecriture.exercice_id,
LigneEcriture.ecriture_id / compte_pcg / debit / credit) pour calculer la
balance finale avant clôture. À enrichir avec journal, lettrage, statut,
lien vers PropositionIA, etc. quand cette étape sera développée en détail.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Journal(str, enum.Enum):
    ACHATS = "achats"
    VENTES = "ventes"
    BANQUE = "banque"
    OD = "od"
    CAISSE = "caisse"


class StatutEcriture(str, enum.Enum):
    BROUILLON = "brouillon"
    VALIDEE = "validee"
    CLOTUREE = "cloturee"


class Ecriture(Base):
    __tablename__ = "ecritures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients_dossiers.id"), nullable=False, index=True
    )
    exercice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercices_comptables.id"), nullable=False, index=True
    )
    journal: Mapped[Journal] = mapped_column(Enum(Journal, name="journal"), nullable=False)
    date_ecriture: Mapped[date] = mapped_column(Date, nullable=False)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    valide_par: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=True
    )
    statut: Mapped[StatutEcriture] = mapped_column(
        Enum(StatutEcriture, name="statut_ecriture"), default=StatutEcriture.BROUILLON
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lignes: Mapped[list["LigneEcriture"]] = relationship(back_populates="ecriture", cascade="all, delete-orphan")


class LigneEcriture(Base):
    __tablename__ = "lignes_ecritures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ecriture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ecritures.id"), nullable=False, index=True
    )
    compte_pcg: Mapped[str] = mapped_column(String(20), nullable=False)
    libelle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    lettrage: Mapped[str | None] = mapped_column(String(20), nullable=True)

    ecriture: Mapped["Ecriture"] = relationship(back_populates="lignes")
