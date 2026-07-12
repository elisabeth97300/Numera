"""
Service applicatif d'authentification.

Rôle : charger/persister via SQLAlchemy et déléguer toute décision métier
(politique de mot de passe, attribution de rôle, isolation multi-tenant) à
app/domain/auth_domain.py. Le hash du mot de passe et la génération des JWT
restent dans app/core/security.py (ils ont besoin de vraies bibliothèques
cryptographiques, contrairement au reste qui est logique pure).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain import auth_domain as domain
from app.models.organisation import Organisation, RoleUtilisateur, Utilisateur


def _tokens_pour(utilisateur: Utilisateur) -> dict:
    return {
        "access_token": create_access_token(utilisateur.id, utilisateur.role.value, utilisateur.organisation_id),
        "refresh_token": create_refresh_token(utilisateur.id),
        "token_type": "bearer",
        "user": utilisateur,
    }


def inscrire_cabinet(db: Session, organisation_nom: str, email: str, mot_de_passe: str) -> dict:
    """
    Crée une nouvelle Organisation (cabinet) et son premier utilisateur, qui
    devient automatiquement admin (règle appliquée par le domaine).
    """
    email_existant = db.scalar(select(Utilisateur).where(Utilisateur.email == email.strip().lower()))
    if email_existant is not None:
        raise domain.AuthError("Un compte existe déjà avec cet email")

    # Le domaine valide le mot de passe, normalise l'email, et détermine le
    # rôle (ADMIN, car role_createur=None = premier utilisateur du cabinet).
    utilisateur_valide = domain.preparer_creation_utilisateur(
        email=email,
        mot_de_passe=mot_de_passe,
        role_demande=domain.RoleUtilisateur.ADMIN,
        role_createur=None,
    )

    organisation = Organisation(nom=organisation_nom)
    db.add(organisation)
    db.flush()  # pour obtenir organisation.id avant de créer l'utilisateur

    utilisateur = Utilisateur(
        organisation_id=organisation.id,
        email=utilisateur_valide.email,
        password_hash=hash_password(mot_de_passe),
        role=RoleUtilisateur(utilisateur_valide.role.value),
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)

    return _tokens_pour(utilisateur)


def inviter_utilisateur(
    db: Session, organisation_id: UUID, role_createur: str, email: str, mot_de_passe: str, role_demande: str
) -> Utilisateur:
    """Un membre existant du cabinet en invite un autre — la règle d'attribution de rôle vient du domaine."""
    email_existant = db.scalar(select(Utilisateur).where(Utilisateur.email == email.strip().lower()))
    if email_existant is not None:
        raise domain.AuthError("Un compte existe déjà avec cet email")

    utilisateur_valide = domain.preparer_creation_utilisateur(
        email=email,
        mot_de_passe=mot_de_passe,
        role_demande=domain.RoleUtilisateur(role_demande),
        role_createur=domain.RoleUtilisateur(role_createur),
    )

    utilisateur = Utilisateur(
        organisation_id=organisation_id,
        email=utilisateur_valide.email,
        password_hash=hash_password(mot_de_passe),
        role=RoleUtilisateur(utilisateur_valide.role.value),
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


def authentifier(db: Session, email: str, mot_de_passe: str) -> dict:
    """Vérifie les identifiants et retourne une nouvelle paire de tokens."""
    utilisateur = db.scalar(select(Utilisateur).where(Utilisateur.email == email.strip().lower()))
    if utilisateur is None or not verify_password(mot_de_passe, utilisateur.password_hash):
        # Message volontairement identique dans les deux cas (email inconnu vs
        # mot de passe incorrect) pour ne pas révéler quels emails existent.
        raise domain.AuthError("Email ou mot de passe incorrect")

    return _tokens_pour(utilisateur)


def rafraichir_access_token(db: Session, refresh_token: str) -> str:
    """Émet un nouvel access token à partir d'un refresh token valide."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise domain.AuthError("Ce token n'est pas un refresh token")

    utilisateur = db.get(Utilisateur, UUID(payload["sub"]))
    if utilisateur is None:
        raise domain.AuthError("Utilisateur introuvable")

    return create_access_token(utilisateur.id, utilisateur.role.value, utilisateur.organisation_id)
