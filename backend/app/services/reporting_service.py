from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.reporting_domain import (
    MouvementCompte,
    calculer_ratios,
    construire_balance,
    construire_bilan,
    construire_compte_resultat,
)
from app.models.ecriture import Ecriture, LigneEcriture
from app.models.exercice import SoldeOuverture


def _solde_ouverture_domaine(db: Session, exercice_id: UUID):
    from app.domain.exercice_domain import LigneSolde, SourceSolde

    rows = db.scalars(select(SoldeOuverture).where(SoldeOuverture.exercice_id == exercice_id))
    return [
        LigneSolde(
            compte_pcg=r.compte_pcg,
            solde_debit=Decimal(str(r.solde_debit)),
            solde_credit=Decimal(str(r.solde_credit)),
            source=SourceSolde(r.source.value),
        )
        for r in rows
    ]


def _mouvements_domaine(db: Session, exercice_id: UUID) -> list[MouvementCompte]:
    rows = db.execute(
        select(LigneEcriture.compte_pcg, LigneEcriture.debit, LigneEcriture.credit)
        .join(Ecriture, LigneEcriture.ecriture_id == Ecriture.id)
        .where(Ecriture.exercice_id == exercice_id)
    ).all()
    return [MouvementCompte(compte_pcg=c, debit=Decimal(str(d or 0)), credit=Decimal(str(cr or 0))) for c, d, cr in rows]


def obtenir_balance(db: Session, exercice_id: UUID):
    solde_ouverture = _solde_ouverture_domaine(db, exercice_id)
    mouvements = _mouvements_domaine(db, exercice_id)
    return construire_balance(solde_ouverture, mouvements)


def obtenir_grand_livre(db: Session, exercice_id: UUID, compte_pcg: str | None = None):
    stmt = (
        select(
            LigneEcriture.compte_pcg,
            LigneEcriture.libelle,
            LigneEcriture.debit,
            LigneEcriture.credit,
            Ecriture.date_ecriture,
            Ecriture.id,
        )
        .join(Ecriture, LigneEcriture.ecriture_id == Ecriture.id)
        .where(Ecriture.exercice_id == exercice_id)
        .order_by(Ecriture.date_ecriture)
    )
    if compte_pcg:
        stmt = stmt.where(LigneEcriture.compte_pcg == compte_pcg)
    return db.execute(stmt).all()


def obtenir_bilan(db: Session, exercice_id: UUID):
    balance = obtenir_balance(db, exercice_id)
    return construire_bilan(balance)


def obtenir_compte_resultat(db: Session, exercice_id: UUID):
    balance = obtenir_balance(db, exercice_id)
    return construire_compte_resultat(balance)


def obtenir_analyse(db: Session, exercice_id: UUID):
    compte_resultat = obtenir_compte_resultat(db, exercice_id)
    return calculer_ratios(compte_resultat)
