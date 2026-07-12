"""
Sécurité : hash des mots de passe, émission/vérification des JWT, dépendances
FastAPI pour récupérer l'utilisateur courant et vérifier son rôle.

Étape 1 du plan (Auth + modèles Organisation/Utilisateur/Client) doit fournir
le modèle Utilisateur réel — ce fichier suppose sa structure minimale
(id, email, role, organisation_id) telle que décrite dans le document
d'architecture.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, expires_delta: timedelta, extra_claims: dict[str, Any] | None = None) -> str:
    to_encode: dict[str, Any] = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, role: str, organisation_id: UUID) -> str:
    return _create_token(
        subject=str(user_id),
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        extra_claims={"role": role, "organisation_id": str(organisation_id), "type": "access"},
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        subject=str(user_id),
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
        extra_claims={"type": "refresh"},
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")


class CurrentUser:
    """Objet léger représentant l'utilisateur authentifié, extrait du JWT."""

    def __init__(self, id: UUID, role: str, organisation_id: UUID):
        self.id = id
        self.role = role
        self.organisation_id = organisation_id


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> CurrentUser:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Type de token invalide")
    return CurrentUser(
        id=UUID(payload["sub"]),
        role=payload["role"],
        organisation_id=UUID(payload["organisation_id"]),
    )


def require_role(*allowed_roles: str):
    """Dépendance factory : `Depends(require_role("admin"))` restreint la route à ce(s) rôle(s)."""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle requis : {', '.join(allowed_roles)}",
            )
        return current_user

    return dependency
