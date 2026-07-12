from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.domain.reconciliation_domain import RapprochementError
from app.schemas.reconciliation import ImportReleveResponse, LigneReleveOut, ValiderLettrageRequest
from app.services import reconciliation_service

router = APIRouter(prefix="/clients/{client_id}/rapprochement", tags=["rapprochement-bancaire"])


@router.post("/import", response_model=ImportReleveResponse, status_code=status.HTTP_201_CREATED)
async def importer_releve(
    client_id: UUID,
    fichier: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Importe un relevé bancaire (CSV) et propose immédiatement un
    rapprochement avec les écritures existantes du compte banque.
    """
    contenu = await fichier.read()
    try:
        resultat = reconciliation_service.importer_releve(db, client_id, contenu)
    except RapprochementError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    solde = resultat["solde"]
    rapprochements_par_id = resultat["rapprochements_par_id"]

    lignes_out = []
    for l in resultat["lignes"]:
        rapprochement = rapprochements_par_id.get(str(l.id))
        candidats = rapprochement.candidats_alternatifs if rapprochement else []
        lignes_out.append(
            {
                "id": l.id,
                "date_operation": l.date_operation,
                "libelle": l.libelle,
                "montant": l.montant,
                "statut": l.statut.value,
                "ligne_ecriture_id": l.ligne_ecriture_id,
                "code_lettrage": l.code_lettrage,
                "candidats_alternatifs": [UUID(c) for c in candidats],
            }
        )

    return {
        "lignes": lignes_out,
        "nombre_rapprochees": solde.nombre_rapprochees,
        "nombre_a_verifier": solde.nombre_a_verifier,
        "nombre_non_rapprochees": solde.nombre_non_rapprochees,
        "taux_rapprochement": solde.taux_rapprochement(),
    }


@router.get("", response_model=list[LigneReleveOut])
def lister_lignes(
    client_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lignes = reconciliation_service.lister_lignes_releve(db, client_id)
    return [
        {
            "id": l.id,
            "date_operation": l.date_operation,
            "libelle": l.libelle,
            "montant": l.montant,
            "statut": l.statut.value,
            "ligne_ecriture_id": l.ligne_ecriture_id,
            "code_lettrage": l.code_lettrage,
            "candidats_alternatifs": [],
        }
        for l in lignes
    ]


@router.post("/{ligne_releve_id}/valider", response_model=LigneReleveOut)
def valider_lettrage(
    client_id: UUID,
    ligne_releve_id: UUID,
    payload: ValiderLettrageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validation manuelle d'une ligne ambiguë ou non rapprochée automatiquement."""
    try:
        ligne = reconciliation_service.valider_lettrage(db, ligne_releve_id, payload.ligne_ecriture_id)
    except RapprochementError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {
        "id": ligne.id,
        "date_operation": ligne.date_operation,
        "libelle": ligne.libelle,
        "montant": ligne.montant,
        "statut": ligne.statut.value,
        "ligne_ecriture_id": ligne.ligne_ecriture_id,
        "code_lettrage": ligne.code_lettrage,
        "candidats_alternatifs": [],
    }
