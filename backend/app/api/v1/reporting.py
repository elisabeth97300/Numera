from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.services import reporting_service

router = APIRouter(prefix="/clients/{client_id}", tags=["reporting"])


@router.get("/balance")
def balance(
    client_id: UUID,
    exercice_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comptes = reporting_service.obtenir_balance(db, exercice_id)
    return [{"compte_pcg": c.compte_pcg, "total_debit": c.total_debit, "total_credit": c.total_credit, "solde": c.solde()} for c in comptes]


@router.get("/grand-livre")
def grand_livre(
    client_id: UUID,
    exercice_id: UUID,
    compte: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lignes = reporting_service.obtenir_grand_livre(db, exercice_id, compte)
    return [
        {
            "compte_pcg": compte_pcg,
            "libelle": libelle,
            "debit": debit,
            "credit": credit,
            "date_ecriture": date_ecriture,
            "ecriture_id": ecriture_id,
        }
        for compte_pcg, libelle, debit, credit, date_ecriture, ecriture_id in lignes
    ]


@router.get("/bilan")
def bilan(
    client_id: UUID,
    exercice_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = reporting_service.obtenir_bilan(db, exercice_id)
    return {
        "actif": [{"compte_pcg": p.compte_pcg, "libelle": p.libelle, "montant": p.montant} for p in b.actif],
        "passif": [{"compte_pcg": p.compte_pcg, "libelle": p.libelle, "montant": p.montant} for p in b.passif],
        "total_actif": b.total_actif(),
        "total_passif": b.total_passif(),
        "equilibre": b.est_equilibre(),
    }


@router.get("/compte-resultat")
def compte_resultat(
    client_id: UUID,
    exercice_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = reporting_service.obtenir_compte_resultat(db, exercice_id)
    return {
        "charges": [{"compte_pcg": p.compte_pcg, "libelle": p.libelle, "montant": p.montant} for p in cr.charges],
        "produits": [{"compte_pcg": p.compte_pcg, "libelle": p.libelle, "montant": p.montant} for p in cr.produits],
        "total_charges": cr.total_charges(),
        "total_produits": cr.total_produits(),
        "resultat_net": cr.resultat_net(),
    }


@router.get("/analyse-financiere")
def analyse_financiere(
    client_id: UUID,
    exercice_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ratios = reporting_service.obtenir_analyse(db, exercice_id)
    return {
        "resultat_net": ratios.resultat_net,
        "total_charges": ratios.total_charges,
        "total_produits": ratios.total_produits,
        "taux_marge": ratios.taux_marge,
    }
