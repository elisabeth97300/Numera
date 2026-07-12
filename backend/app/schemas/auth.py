"""Schémas Pydantic pour l'authentification et la gestion des utilisateurs."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Inscription d'un nouveau cabinet : crée l'Organisation ET son premier utilisateur (admin)."""

    organisation_nom: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    mot_de_passe: str = Field(..., min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    mot_de_passe: str


class InviterUtilisateurRequest(BaseModel):
    """Un admin (ou, avec restriction, un comptable) invite un nouveau membre du cabinet."""

    email: EmailStr
    mot_de_passe: str = Field(..., min_length=10, max_length=128)
    role: str = Field(..., pattern="^(admin|comptable|assistant)$")


class UserOut(BaseModel):
    id: UUID
    email: str
    role: str
    organisation_id: UUID

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
