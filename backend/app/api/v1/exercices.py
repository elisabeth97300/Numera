"""
Routes API pour les exercices comptables : création, démarrage (avec ou sans
solde de reprise), clôture, réouverture exceptionnelle.

Dépendances supposées déjà en place (étape 1) : get_db (session SQLAlchemy),
get_current_user (JWT), require_role (contrôle de rôle).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.domain.exercice_domain import ExerciceError
from app.models.exercice import ExerciceComptable
from app.schemas.exercice import (
    ClotureExerciceResponse,
    ExerciceCreate,
    ExerciceOut,
    SoldeOuvertureSaisieManuelle,
)
from app.services import exercice_service

router = APIRouter(prefix="/clients/{client_id}/exercices", tags=["exercices"])
router_global = APIRouter(prefix="/exercices", tags=["exercices"])


@router.get("", response_model=list[ExerciceOut])
def lister_exercices(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from sqlalchemy import select

    return list(db.scalars(select(ExerciceComptable).where(ExerciceComptable.client_id == client_id)))


@router.post("", response_model=ExerciceOut, status_code=status.HTTP_201_CREATED)
def creer_exercice(
    client_id: UUID,
    payload: ExerciceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crée un exercice comptable pour un client.
    - `origine = nouveau` : l'exercice pourra démarrer sans solde d'ouverture.
    - `origine = repris` : un solde d'ouverture équilibré sera exigé au démarrage
      (voir `POST /exercices/{id}/solde-ouverture`).
    """
    exercice = ExerciceComptable(
        client_id=client_id,
        date_debut=payload.date_debut,
        date_fin=payload.date_fin,
        origine=payload.origine.value,
        exercice_precedent_id=payload.exercice_precedent_id,
    )
    db.add(exercice)
    db.commit()
    db.refresh(exercice)
    return exercice


@router_global.post("/{exercice_id}/solde-ouverture", response_model=ExerciceOut)
def saisir_solde_ouverture(
    exercice_id: UUID,
    payload: SoldeOuvertureSaisieManuelle,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Saisie manuelle du bilan d'ouverture d'un dossier repris, compte par
    compte. Fait passer l'exercice à EN_COURS si le solde est équilibré.

    C'est l'endpoint clé pour répondre au besoin : "un cabinet qui reprend une
    entreprise déjà existante, avec des exercices déjà clôturés ailleurs, doit
    pouvoir démarrer sans ressaisir tout l'historique."
    """
    lignes = [l.model_dump() for l in payload.lignes]
    try:
        exercice = exercice_service.demarrer_exercice(db, exercice_id, lignes)
    except ExerciceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return exercice


@router_global.post("/{exercice_id}/demarrer", response_model=ExerciceOut)
def demarrer_exercice_nouveau(
    exercice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Démarre un exercice `nouveau` (aucun solde d'ouverture requis)."""
    try:
        exercice = exercice_service.demarrer_exercice(db, exercice_id, lignes=None)
    except ExerciceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return exercice


@router_global.post("/{exercice_id}/cloturer", response_model=ClotureExerciceResponse)
def cloturer_exercice(
    exercice_id: UUID,
    creer_exercice_suivant: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Clôture un exercice : vérifie l'équilibre global de la balance, verrouille
    les écritures, et (par défaut) crée immédiatement l'exercice suivant avec
    son solde d'ouverture pré-rempli automatiquement.
    """
    try:
        resultat = exercice_service.cloturer_exercice(db, exercice_id, creer_exercice_suivant)
    except ExerciceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return resultat


@router_global.post("/{exercice_id}/reouvrir", response_model=ExerciceOut)
def reouvrir_exercice(
    exercice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    """
    Réouverture exceptionnelle d'un exercice clôturé. Réservé au rôle `admin`
    par `require_role` (double vérification : ici au niveau route, et dans le
    domaine par sécurité — cf. exercice_domain.reouvrir_exercice).
    Doit systématiquement générer un événement dans le module Audit (TODO:
    brancher sur audit_service une fois ce module codé).
    """
    try:
        exercice = exercice_service.reouvrir_exercice(db, exercice_id, current_user.role)
    except ExerciceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return exercice


@router_global.get("/{exercice_id}", response_model=ExerciceOut)
def obtenir_exercice(
    exercice_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    exercice = db.get(ExerciceComptable, exercice_id)
    if exercice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable")
    return exercice
