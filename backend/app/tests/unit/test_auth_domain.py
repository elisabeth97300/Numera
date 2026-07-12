"""
Tests de la couche domaine (app/domain/auth_domain.py).
Aucune dépendance externe : stdlib uniquement.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/app/

from domain.auth_domain import (  # noqa: E402
    AuthError,
    AutorisationError,
    RoleUtilisateur,
    determiner_role_nouvel_utilisateur,
    preparer_creation_utilisateur,
    valider_force_mot_de_passe,
    verifier_appartenance_organisation,
)


class TestPolitiqueMotDePasse(unittest.TestCase):
    def test_mot_de_passe_trop_court_refuse(self):
        with self.assertRaises(AuthError):
            valider_force_mot_de_passe("abc123")

    def test_mot_de_passe_sans_chiffre_refuse(self):
        with self.assertRaises(AuthError):
            valider_force_mot_de_passe("motdepasselong")

    def test_mot_de_passe_sans_lettre_refuse(self):
        with self.assertRaises(AuthError):
            valider_force_mot_de_passe("1234567890")

    def test_mot_de_passe_trivial_refuse(self):
        with self.assertRaises(AuthError):
            valider_force_mot_de_passe("Password1")

    def test_mot_de_passe_contenant_email_refuse(self):
        with self.assertRaises(AuthError):
            valider_force_mot_de_passe("sophie12345", email="sophie@cabinet-martin.fr")

    def test_mot_de_passe_valide_accepte(self):
        valider_force_mot_de_passe("Tresor42Cabinet", email="sophie@cabinet-martin.fr")  # ne doit pas lever


class TestAttributionRole(unittest.TestCase):
    def test_premier_utilisateur_organisation_devient_admin(self):
        role = determiner_role_nouvel_utilisateur(RoleUtilisateur.COMPTABLE, role_createur=None)
        self.assertEqual(role, RoleUtilisateur.ADMIN)

    def test_admin_peut_creer_un_autre_admin(self):
        role = determiner_role_nouvel_utilisateur(RoleUtilisateur.ADMIN, role_createur=RoleUtilisateur.ADMIN)
        self.assertEqual(role, RoleUtilisateur.ADMIN)

    def test_admin_peut_creer_un_comptable(self):
        role = determiner_role_nouvel_utilisateur(RoleUtilisateur.COMPTABLE, role_createur=RoleUtilisateur.ADMIN)
        self.assertEqual(role, RoleUtilisateur.COMPTABLE)

    def test_comptable_ne_peut_pas_creer_un_admin(self):
        with self.assertRaises(AutorisationError):
            determiner_role_nouvel_utilisateur(RoleUtilisateur.ADMIN, role_createur=RoleUtilisateur.COMPTABLE)

    def test_comptable_ne_peut_pas_creer_un_autre_comptable(self):
        with self.assertRaises(AutorisationError):
            determiner_role_nouvel_utilisateur(RoleUtilisateur.COMPTABLE, role_createur=RoleUtilisateur.COMPTABLE)

    def test_comptable_peut_creer_un_assistant(self):
        role = determiner_role_nouvel_utilisateur(RoleUtilisateur.ASSISTANT, role_createur=RoleUtilisateur.COMPTABLE)
        self.assertEqual(role, RoleUtilisateur.ASSISTANT)

    def test_assistant_ne_peut_pas_creer_un_admin(self):
        with self.assertRaises(AutorisationError):
            determiner_role_nouvel_utilisateur(RoleUtilisateur.ADMIN, role_createur=RoleUtilisateur.ASSISTANT)


class TestIsolationMultiTenant(unittest.TestCase):
    def test_meme_organisation_ne_leve_rien(self):
        verifier_appartenance_organisation("org-1", "org-1")  # ne doit pas lever

    def test_organisation_differente_est_bloquee(self):
        with self.assertRaises(AutorisationError):
            verifier_appartenance_organisation("org-1", "org-2")


class TestPreparerCreationUtilisateur(unittest.TestCase):
    def test_inscription_cabinet_donne_admin_et_email_normalise(self):
        resultat = preparer_creation_utilisateur(
            email="  Sophie@Cabinet-Martin.fr  ",
            mot_de_passe="Tresor42Cabinet",
            role_demande=RoleUtilisateur.COMPTABLE,  # ignoré : c'est le premier utilisateur
            role_createur=None,
        )
        self.assertEqual(resultat.email, "sophie@cabinet-martin.fr")
        self.assertEqual(resultat.role, RoleUtilisateur.ADMIN)

    def test_mot_de_passe_faible_bloque_avant_toute_creation(self):
        with self.assertRaises(AuthError):
            preparer_creation_utilisateur(
                email="nouveau@cabinet-martin.fr",
                mot_de_passe="123",
                role_demande=RoleUtilisateur.ASSISTANT,
                role_createur=RoleUtilisateur.ADMIN,
            )

    def test_permission_insuffisante_bloque_avant_toute_creation(self):
        with self.assertRaises(AutorisationError):
            preparer_creation_utilisateur(
                email="nouveau@cabinet-martin.fr",
                mot_de_passe="MotDePasseValide1",
                role_demande=RoleUtilisateur.ADMIN,
                role_createur=RoleUtilisateur.ASSISTANT,
            )


if __name__ == "__main__":
    unittest.main()
