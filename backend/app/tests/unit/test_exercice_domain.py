"""
Tests de la couche domaine (app/domain/exercice_domain.py).

Aucune dépendance externe : uniquement le stdlib (unittest) et le module testé.
À lancer avec : python -m pytest app/tests/unit/test_exercice_domain.py
ou simplement : python -m unittest app/tests/unit/test_exercice_domain.py
"""

import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/app/

from domain.exercice_domain import (  # noqa: E402
    BalanceCompte,
    Exercice,
    ExerciceError,
    LigneSolde,
    OrigineExercice,
    SourceSolde,
    StatutExercice,
    calculer_solde_ouverture_suivant,
    cloturer_exercice,
    demarrer_exercice,
    reouvrir_exercice,
    valider_equilibre_solde_ouverture,
    verifier_ecriture_modifiable,
)


def make_exercice(origine: OrigineExercice, statut: StatutExercice = StatutExercice.NON_DEMARRE) -> Exercice:
    return Exercice(
        id="ex-1",
        client_id="client-1",
        date_debut=date(2026, 1, 1),
        date_fin=date(2026, 12, 31),
        origine=origine,
        statut=statut,
    )


class TestDemarrageExerciceNouveau(unittest.TestCase):
    def test_nouvelle_entreprise_demarre_sans_solde_ouverture(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU)
        demarrer_exercice(exercice)
        self.assertEqual(exercice.statut, StatutExercice.EN_COURS)
        self.assertEqual(exercice.solde_ouverture, [])

    def test_nouvelle_entreprise_refuse_double_demarrage(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU)
        demarrer_exercice(exercice)
        with self.assertRaises(ExerciceError):
            demarrer_exercice(exercice)


class TestDemarrageExerciceRepris(unittest.TestCase):
    def test_dossier_repris_sans_solde_est_refuse(self):
        exercice = make_exercice(OrigineExercice.REPRIS)
        with self.assertRaises(ExerciceError) as ctx:
            demarrer_exercice(exercice, solde_ouverture=None)
        self.assertIn("solde d'ouverture", str(ctx.exception))

    def test_dossier_repris_avec_solde_desequilibre_est_refuse(self):
        exercice = make_exercice(OrigineExercice.REPRIS)
        solde = [
            LigneSolde("512000", solde_debit=Decimal("10000")),  # banque
            LigneSolde("101000", solde_credit=Decimal("9000")),  # capital (manque 1000)
        ]
        with self.assertRaises(ExerciceError) as ctx:
            demarrer_exercice(exercice, solde_ouverture=solde)
        self.assertIn("équilibré", str(ctx.exception))

    def test_dossier_repris_avec_solde_equilibre_demarre(self):
        exercice = make_exercice(OrigineExercice.REPRIS)
        solde = [
            LigneSolde("512000", solde_debit=Decimal("10000")),  # banque
            LigneSolde("101000", solde_credit=Decimal("10000")),  # capital
        ]
        demarrer_exercice(exercice, solde_ouverture=solde)
        self.assertEqual(exercice.statut, StatutExercice.EN_COURS)
        self.assertEqual(len(exercice.solde_ouverture), 2)


class TestValidationEquilibre(unittest.TestCase):
    def test_equilibre_exact_ne_leve_rien(self):
        lignes = [
            LigneSolde("411000", solde_debit=Decimal("500.00")),
            LigneSolde("706000", solde_credit=Decimal("500.00")),
        ]
        valider_equilibre_solde_ouverture(lignes)  # ne doit pas lever

    def test_ecart_meme_faible_est_detecte(self):
        lignes = [
            LigneSolde("411000", solde_debit=Decimal("500.01")),
            LigneSolde("706000", solde_credit=Decimal("500.00")),
        ]
        with self.assertRaises(ExerciceError):
            valider_equilibre_solde_ouverture(lignes)


class TestVerrouillageExerciceCloture(unittest.TestCase):
    def test_exercice_en_cours_autorise_ecriture(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.EN_COURS)
        verifier_ecriture_modifiable(exercice)  # ne doit pas lever

    def test_exercice_cloture_interdit_ecriture(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.CLOTURE)
        with self.assertRaises(ExerciceError) as ctx:
            verifier_ecriture_modifiable(exercice)
        self.assertIn("clôturé", str(ctx.exception))

    def test_exercice_archive_interdit_ecriture(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.ARCHIVE)
        with self.assertRaises(ExerciceError):
            verifier_ecriture_modifiable(exercice)


class TestCalculSoldeOuvertureSuivant(unittest.TestCase):
    def test_comptes_bilan_reportes_et_gestion_remis_a_zero(self):
        balance = [
            BalanceCompte("512000", total_debit=Decimal("15000"), total_credit=Decimal("5000")),  # banque, solde débiteur 10000
            BalanceCompte("401000", total_debit=Decimal("2000"), total_credit=Decimal("6000")),  # fournisseurs, solde créditeur 4000
            BalanceCompte("606000", total_debit=Decimal("3000"), total_credit=Decimal("0")),  # charge, classe 6
            BalanceCompte("706000", total_debit=Decimal("0"), total_credit=Decimal("9000")),  # produit, classe 7
        ]
        solde_suivant = calculer_solde_ouverture_suivant(balance)

        comptes_reportes = {l.compte_pcg for l in solde_suivant}
        # comptes de gestion jamais reportés
        self.assertNotIn("606000", comptes_reportes)
        self.assertNotIn("706000", comptes_reportes)
        # comptes de bilan reportés
        self.assertIn("512000", comptes_reportes)
        self.assertIn("401000", comptes_reportes)
        # résultat = produits(9000) - charges(3000) = 6000 (bénéfice) -> compte 120 au crédit
        self.assertIn("120000", comptes_reportes)

        banque = next(l for l in solde_suivant if l.compte_pcg == "512000")
        self.assertEqual(banque.solde_debit, Decimal("10000"))
        self.assertEqual(banque.solde_credit, Decimal("0"))

        resultat = next(l for l in solde_suivant if l.compte_pcg == "120000")
        self.assertEqual(resultat.solde_credit, Decimal("6000"))
        self.assertEqual(resultat.source, SourceSolde.CLOTURE_AUTO)

    def test_resultat_negatif_va_en_compte_129(self):
        balance = [
            BalanceCompte("606000", total_debit=Decimal("9000"), total_credit=Decimal("0")),
            BalanceCompte("706000", total_debit=Decimal("0"), total_credit=Decimal("3000")),
        ]
        solde_suivant = calculer_solde_ouverture_suivant(balance)
        perte = next(l for l in solde_suivant if l.compte_pcg == "129000")
        self.assertEqual(perte.solde_debit, Decimal("6000"))

    def test_comptes_soldes_a_zero_ne_sont_pas_reportes(self):
        balance = [BalanceCompte("512000", total_debit=Decimal("1000"), total_credit=Decimal("1000"))]
        solde_suivant = calculer_solde_ouverture_suivant(balance)
        self.assertEqual([l for l in solde_suivant if l.compte_pcg == "512000"], [])


class TestClotureExercice(unittest.TestCase):
    def test_cloture_refuse_si_exercice_pas_en_cours(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.NON_DEMARRE)
        with self.assertRaises(ExerciceError):
            cloturer_exercice(exercice, balance_finale=[])

    def test_cloture_refuse_si_balance_desequilibree(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.EN_COURS)
        balance = [BalanceCompte("512000", total_debit=Decimal("100"), total_credit=Decimal("0"))]
        with self.assertRaises(ExerciceError) as ctx:
            cloturer_exercice(exercice, balance_finale=balance)
        self.assertIn("équilibrée", str(ctx.exception))
        # l'exercice ne doit pas être passé à CLOTURE si le refus a lieu
        self.assertEqual(exercice.statut, StatutExercice.EN_COURS)

    def test_cloture_ok_verrouille_et_genere_solde_suivant(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.EN_COURS)
        balance = [
            BalanceCompte("512000", total_debit=Decimal("10000"), total_credit=Decimal("0")),
            BalanceCompte("101000", total_debit=Decimal("0"), total_credit=Decimal("10000")),
        ]
        exercice_cloture, solde_suivant = cloturer_exercice(exercice, balance_finale=balance)
        self.assertEqual(exercice_cloture.statut, StatutExercice.CLOTURE)
        self.assertTrue(len(solde_suivant) >= 1)
        # une fois clôturé, plus aucune écriture ne doit être acceptée
        with self.assertRaises(ExerciceError):
            verifier_ecriture_modifiable(exercice_cloture)


class TestReouverture(unittest.TestCase):
    def test_reouverture_refusee_pour_non_admin(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.CLOTURE)
        with self.assertRaises(ExerciceError):
            reouvrir_exercice(exercice, role_utilisateur="comptable")

    def test_reouverture_acceptee_pour_admin(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.CLOTURE)
        reouvrir_exercice(exercice, role_utilisateur="admin")
        self.assertEqual(exercice.statut, StatutExercice.EN_COURS)

    def test_reouverture_refusee_si_pas_cloture(self):
        exercice = make_exercice(OrigineExercice.NOUVEAU, statut=StatutExercice.EN_COURS)
        with self.assertRaises(ExerciceError):
            reouvrir_exercice(exercice, role_utilisateur="admin")


class TestScenarioBoutEnBout(unittest.TestCase):
    """Reproduit le cas concret soulevé par le client : reprise d'un dossier existant."""

    def test_reprise_dossier_existant_puis_cloture_puis_ouverture_suivante(self):
        # 1. Le cabinet reprend un dossier client dont l'exercice précédent
        #    (géré ailleurs) s'est soldé sur cette balance de clôture, saisie
        #    manuellement par le comptable.
        exercice_2025 = make_exercice(OrigineExercice.REPRIS)
        exercice_2025.id = "ex-2025"
        solde_reprise = [
            LigneSolde("512000", solde_debit=Decimal("25000")),
            LigneSolde("101000", solde_credit=Decimal("20000")),
            LigneSolde("120000", solde_credit=Decimal("5000")),
        ]
        demarrer_exercice(exercice_2025, solde_ouverture=solde_reprise)
        self.assertEqual(exercice_2025.statut, StatutExercice.EN_COURS)

        # 2. L'année se déroule, des écritures sont passées (non modélisées ici,
        #    hors périmètre de ce test), puis on clôture avec la balance finale.
        balance_finale_2025 = [
            BalanceCompte("512000", total_debit=Decimal("40000"), total_credit=Decimal("10000")),
            BalanceCompte("101000", total_debit=Decimal("0"), total_credit=Decimal("20000")),
            BalanceCompte("606000", total_debit=Decimal("8000"), total_credit=Decimal("0")),
            BalanceCompte("706000", total_debit=Decimal("0"), total_credit=Decimal("18000")),
        ]
        exercice_2025, solde_pour_2026 = cloturer_exercice(exercice_2025, balance_finale_2025)
        self.assertEqual(exercice_2025.statut, StatutExercice.CLOTURE)

        # 3. Impossible de repasser une écriture sur 2025 après coup.
        with self.assertRaises(ExerciceError):
            verifier_ecriture_modifiable(exercice_2025)

        # 4. L'exercice 2026 démarre automatiquement avec le solde calculé.
        exercice_2026 = Exercice(
            id="ex-2026",
            client_id="client-1",
            date_debut=date(2026, 1, 1),
            date_fin=date(2026, 12, 31),
            origine=OrigineExercice.REPRIS,  # "repris" du point de vue de l'outil : le solde vient de la clôture précédente
            exercice_precedent_id=exercice_2025.id,
        )
        demarrer_exercice(exercice_2026, solde_ouverture=solde_pour_2026)
        self.assertEqual(exercice_2026.statut, StatutExercice.EN_COURS)
        self.assertTrue(all(l.source == SourceSolde.CLOTURE_AUTO for l in exercice_2026.solde_ouverture))


if __name__ == "__main__":
    unittest.main()
