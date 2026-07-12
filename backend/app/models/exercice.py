"""
Modèles SQLAlchemy pour les exercices comptables et les soldes d'ouverture.

Ces modèles ne portent AUCUNE logique métier eux-mêmes (pas de calcul de
clôture, pas de validation d'équilibre) : ce sont de simples structures de
persistance. Toutes les règles vivent dans app/domain/exercice_domain.py — les
services (app/services/exercice_service.py, à venir) font le pont entre les
deux : ils chargent des lignes depuis la base, les convertissent en objets du
domaine, appellent les fonctions métier, puis persistent le résultat.

Nécessite : sqlalchemy>=2.0 (cf. requirements.txt)
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StatutExercice(str, enum.Enum):
    NON_DEMARRE = "non_demarre"
    EN_COURS = "en_cours"
    CLOTURE = "cloture"
    ARCHIVE = "archive"


class OrigineExercice(str, enum.Enum):
    NOUVEAU = "nouveau"
    REPRIS = "repris"


class SourceSolde(str, enum.Enum):
    SAISIE_MANUELLE = "saisie_manuelle"
    IMPORT_FEC = "import_fec"
    CLOTURE_AUTO = "cloture_auto"


class ExerciceComptable(Base):
    __tablename__ = "exercices_comptables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients_dossiers.id"), nullable=False, index=True
    )
    date_debut: Mapped[date] = mapped_column(Date, nullable=False)
    date_fin: Mapped[date] = mapped_column(Date, nullable=False)
    statut: Mapped[StatutExercice] = mapped_column(
        Enum(StatutExercice, name="statut_exercice"), default=StatutExercice.NON_DEMARRE, nullable=False
    )
    origine: Mapped[OrigineExercice] = mapped_column(
        Enum(OrigineExercice, name="origine_exercice"), nullable=False
    )
    date_cloture: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cloture_par: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=True
    )
    exercice_precedent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercices_comptables.id"), nullable=True
    )

    soldes_ouverture: Mapped[list["SoldeOuverture"]] = relationship(
        back_populates="exercice", cascade="all, delete-orphan"
    )


class SoldeOuverture(Base):
    """
    Une ligne du bilan d'ouverture d'un exercice : uniquement pour un exercice
    `origine = repris`, ou générée automatiquement pour l'exercice suivant un
    exercice clôturé dans l'outil (source = cloture_auto).
    """

    __tablename__ = "soldes_ouverture"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercices_comptables.id"), nullable=False, index=True
    )
    compte_pcg: Mapped[str] = mapped_column(String(20), nullable=False)
    solde_debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    solde_credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    source: Mapped[SourceSolde] = mapped_column(Enum(SourceSolde, name="source_solde"), nullable=False)

    exercice: Mapped["ExerciceComptable"] = relationship(back_populates="soldes_ouverture")
