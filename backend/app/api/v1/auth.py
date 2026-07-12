"""Routes API pour l'authentification : inscription du cabinet, connexion, rafraîchissement, invitation."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.domain.auth_domain import AuthError, AutorisationError
from app.models.organisation import Utilisateur
from app.schemas.auth import (
    AccessTokenResponse,
    InviterUtilisateurRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Inscription d'un nouveau cabinet : crée l'Organisation et son premier
    utilisateur, qui devient automatiquement administrateur.
    """
    try:
        return auth_service.inscrire_cabinet(db, payload.organisation_nom, payload.email, payload.mot_de_passe)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.authentifier(db, payload.email, payload.mot_de_passe)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        access_token = auth_service.rafraichir_access_token(db, payload.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    utilisateur = db.get(Utilisateur, current_user.id)
    if utilisateur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    return utilisateur


@router.post("/invite", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def inviter(
    payload: InviterUtilisateurRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invite un nouveau membre dans le cabinet de l'utilisateur connecté.
    La règle d'attribution de rôle (qui peut créer quel rôle) est appliquée
    par le domaine, pas ici — cf. auth_domain.determiner_role_nouvel_utilisateur.
    """
    try:
        return auth_service.inviter_utilisateur(
            db,
            organisation_id=current_user.organisation_id,
            role_createur=current_user.role,
            email=payload.email,
            mot_de_passe=payload.mot_de_passe,
            role_demande=payload.role,
        )
    except AutorisationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
