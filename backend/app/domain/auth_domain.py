"""
Logique métier pure pour l'authentification, la gestion des utilisateurs et
l'isolation multi-tenant. Comme pour exercice_domain.py : aucune dépendance à
un framework, pas de cryptographie ici (le hash du mot de passe et le JWT
restent dans app/core/security.py, qui a besoin de vraies bibliothèques) —
uniquement les règles métier, testables avec le seul stdlib.
"""

import re
from dataclasses import dataclass
from enum import Enum


class RoleUtilisateur(str, Enum):
    ADMIN = "admin"
    COMPTABLE = "comptable"
    ASSISTANT = "assistant"


class AuthError(Exception):
    """Erreur métier liée à l'authentification ou à la gestion des utilisateurs."""


class AutorisationError(Exception):
    """
    Erreur d'isolation multi-tenant ou de permission insuffisante.
    Séparée de AuthError pour que la couche API puisse répondre 403 plutôt
    que 401/422 sans avoir à inspecter le message d'erreur.
    """


# Liste volontairement courte : ce n'est pas un dictionnaire de mots de passe
# exhaustif, seulement un filet contre les valeurs les plus évidentes qu'un
# contrôle de longueur/complexité ne suffit pas à écarter.
MOTS_DE_PASSE_TRIVIAUX = {
    "password", "password1", "azertyuiop", "123456789", "motdepasse",
    "comptable1", "administrateur",
}


def valider_force_mot_de_passe(mot_de_passe: str, email: str | None = None) -> None:
    """
    Politique de mot de passe minimale mais réelle :
    - au moins 10 caractères ;
    - au moins une lettre et un chiffre ;
    - pas une valeur triviale connue ;
    - ne contient pas la partie locale de l'email (avant le @), pour éviter
      le cas trop fréquent "email: a@cabinet.fr / mdp: a1234567".
    """
    if len(mot_de_passe) < 10:
        raise AuthError("Le mot de passe doit contenir au moins 10 caractères")

    if not re.search(r"[a-zA-Z]", mot_de_passe) or not re.search(r"\d", mot_de_passe):
        raise AuthError("Le mot de passe doit contenir au moins une lettre et un chiffre")

    if mot_de_passe.lower() in MOTS_DE_PASSE_TRIVIAUX:
        raise AuthError("Ce mot de passe est trop courant, choisis-en un autre")

    if email:
        partie_locale = email.split("@")[0].lower()
        if len(partie_locale) >= 3 and partie_locale in mot_de_passe.lower():
            raise AuthError("Le mot de passe ne doit pas contenir ton adresse email")


def determiner_role_nouvel_utilisateur(
    role_demande: RoleUtilisateur, role_createur: RoleUtilisateur | None
) -> RoleUtilisateur:
    """
    Règle métier d'attribution des rôles :
    - le tout premier utilisateur d'une organisation (role_createur=None, cas
      de l'inscription du cabinet) devient automatiquement admin, quel que
      soit ce qui a été demandé — c'est lui qui crée le cabinet ;
    - ensuite, seul un admin peut créer un autre admin ;
    - un comptable ou un assistant ne peut créer que des assistants (jamais
      d'admin, jamais d'autre comptable), pour éviter qu'un compte à
      permissions limitées ne s'auto-élève.
    """
    if role_createur is None:
        return RoleUtilisateur.ADMIN

    if role_createur == RoleUtilisateur.ADMIN:
        return role_demande

    if role_demande != RoleUtilisateur.ASSISTANT:
        raise AutorisationError(
            "Seul un administrateur peut créer un compte comptable ou administrateur"
        )
    return RoleUtilisateur.ASSISTANT


def verifier_appartenance_organisation(
    organisation_id_ressource: str, organisation_id_utilisateur: str
) -> None:
    """
    Garde-fou central de l'isolation multi-tenant : à appeler avant toute
    lecture/écriture sur une ressource (client, exercice, écriture...) pour
    vérifier qu'elle appartient bien à l'organisation de l'utilisateur
    authentifié. Un cabinet ne doit jamais pouvoir voir/modifier les données
    d'un autre cabinet, même en devinant un identifiant.
    """
    if organisation_id_ressource != organisation_id_utilisateur:
        raise AutorisationError("Cette ressource n'appartient pas à votre organisation")


@dataclass
class NouvelUtilisateurValide:
    email: str
    role: RoleUtilisateur


def preparer_creation_utilisateur(
    email: str,
    mot_de_passe: str,
    role_demande: RoleUtilisateur,
    role_createur: RoleUtilisateur | None,
) -> NouvelUtilisateurValide:
    """
    Point d'entrée unique du domaine pour la création d'un utilisateur :
    applique la politique de mot de passe puis la règle d'attribution de
    rôle. La couche service n'a plus qu'à persister le résultat.
    """
    valider_force_mot_de_passe(mot_de_passe, email)
    role_final = determiner_role_nouvel_utilisateur(role_demande, role_createur)
    return NouvelUtilisateurValide(email=email.strip().lower(), role=role_final)
