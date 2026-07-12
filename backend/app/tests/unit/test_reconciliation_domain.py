import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.reconciliation_domain import (  # noqa: E402
    LigneEcritureBanque,
    LigneReleve,
    RapprochementError,
    StatutRapprochement,
    calculer_solde_rapprochement,
    generer_code_lettrage,
    proposer_rapprochements,
    valider_lettrage_manuel,
)


class TestProposerRapprochements(unittest.TestCase):
    def test_correspondance_exacte_unique(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR EDF", Decimal("-221.04"))]
        ecritures = [LigneEcritureBanque("e1", date(2026, 7, 4), "EDF", debit=Decimal("0"), credit=Decimal("221.04"))]
        resultats = proposer_rapprochements(releve, ecritures)
        self.assertEqual(resultats[0].statut, StatutRapprochement.RAPPROCHE_AUTOMATIQUE)
        self.assertEqual(resultats[0].ligne_ecriture_id, "e1")

    def test_aucun_candidat_non_rapproche(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR INCONNU", Decimal("-500"))]
        ecritures = [LigneEcritureBanque("e1", date(2026, 7, 4), "EDF", debit=Decimal("0"), credit=Decimal("221.04"))]
        resultats = proposer_rapprochements(releve, ecritures)
        self.assertEqual(resultats[0].statut, StatutRapprochement.NON_RAPPROCHE)
        self.assertIsNone(resultats[0].ligne_ecriture_id)

    def test_deux_candidats_meme_montant_dates_differentes_departagees_par_date_exacte(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR EDF", Decimal("-100"))]
        ecritures = [
            LigneEcritureBanque("e1", date(2026, 7, 4), "EDF", debit=Decimal("0"), credit=Decimal("100")),
            LigneEcritureBanque("e2", date(2026, 7, 6), "AUTRE", debit=Decimal("0"), credit=Decimal("100")),
        ]
        resultats = proposer_rapprochements(releve, ecritures)
        self.assertEqual(resultats[0].statut, StatutRapprochement.RAPPROCHE_AUTOMATIQUE)
        self.assertEqual(resultats[0].ligne_ecriture_id, "e1")

    def test_deux_candidats_ambigus_marques_a_verifier(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR", Decimal("-100"))]
        ecritures = [
            LigneEcritureBanque("e1", date(2026, 7, 5), "A", debit=Decimal("0"), credit=Decimal("100")),
            LigneEcritureBanque("e2", date(2026, 7, 6), "B", debit=Decimal("0"), credit=Decimal("100")),
        ]
        resultats = proposer_rapprochements(releve, ecritures)
        self.assertEqual(resultats[0].statut, StatutRapprochement.A_VERIFIER)
        self.assertEqual(set(resultats[0].candidats_alternatifs), {"e1", "e2"})

    def test_ecriture_deja_utilisee_non_reutilisee(self):
        releve = [
            LigneReleve("r1", date(2026, 7, 4), "VIR A", Decimal("-100")),
            LigneReleve("r2", date(2026, 7, 4), "VIR B", Decimal("-100")),
        ]
        ecritures = [LigneEcritureBanque("e1", date(2026, 7, 4), "A", debit=Decimal("0"), credit=Decimal("100"))]
        resultats = proposer_rapprochements(releve, ecritures)
        self.assertEqual(resultats[0].statut, StatutRapprochement.RAPPROCHE_AUTOMATIQUE)
        self.assertEqual(resultats[1].statut, StatutRapprochement.NON_RAPPROCHE)

    def test_encaissement_positif_matche_debit_banque(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR CLIENT", Decimal("500"))]
        ecritures = [LigneEcritureBanque("e1", date(2026, 7, 4), "Client X", debit=Decimal("500"), credit=Decimal("0"))]
        resultats = proposer_rapprochements(releve, ecritures)
        self.assertEqual(resultats[0].statut, StatutRapprochement.RAPPROCHE_AUTOMATIQUE)

    def test_hors_tolerance_de_date_non_rapproche(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR", Decimal("-100"))]
        ecritures = [LigneEcritureBanque("e1", date(2026, 8, 1), "A", debit=Decimal("0"), credit=Decimal("100"))]
        resultats = proposer_rapprochements(releve, ecritures)
        self.assertEqual(resultats[0].statut, StatutRapprochement.NON_RAPPROCHE)


class TestValiderLettrageManuel(unittest.TestCase):
    def test_choix_parmi_candidats_valide(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR", Decimal("-100"))]
        ecritures = [
            LigneEcritureBanque("e1", date(2026, 7, 5), "A", debit=Decimal("0"), credit=Decimal("100")),
            LigneEcritureBanque("e2", date(2026, 7, 6), "B", debit=Decimal("0"), credit=Decimal("100")),
        ]
        rapprochement = proposer_rapprochements(releve, ecritures)[0]
        resultat = valider_lettrage_manuel(rapprochement, "e2")
        self.assertEqual(resultat.statut, StatutRapprochement.RAPPROCHE_MANUEL)
        self.assertEqual(resultat.ligne_ecriture_id, "e2")

    def test_choix_hors_candidats_refuse(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR", Decimal("-100"))]
        ecritures = [
            LigneEcritureBanque("e1", date(2026, 7, 5), "A", debit=Decimal("0"), credit=Decimal("100")),
            LigneEcritureBanque("e2", date(2026, 7, 6), "B", debit=Decimal("0"), credit=Decimal("100")),
        ]
        rapprochement = proposer_rapprochements(releve, ecritures)[0]
        with self.assertRaises(RapprochementError):
            valider_lettrage_manuel(rapprochement, "e999")

    def test_deja_rapproche_automatiquement_refuse_une_correction(self):
        releve = [LigneReleve("r1", date(2026, 7, 4), "VIR", Decimal("-100"))]
        ecritures = [LigneEcritureBanque("e1", date(2026, 7, 4), "A", debit=Decimal("0"), credit=Decimal("100"))]
        rapprochement = proposer_rapprochements(releve, ecritures)[0]
        with self.assertRaises(RapprochementError):
            valider_lettrage_manuel(rapprochement, "e1")


class TestGenererCodeLettrage(unittest.TestCase):
    def test_premiers_codes(self):
        self.assertEqual(generer_code_lettrage(0), "A")
        self.assertEqual(generer_code_lettrage(1), "B")
        self.assertEqual(generer_code_lettrage(25), "Z")

    def test_apres_z_deux_lettres(self):
        self.assertEqual(generer_code_lettrage(26), "AA")
        self.assertEqual(generer_code_lettrage(27), "AB")

    def test_index_negatif_refuse(self):
        with self.assertRaises(RapprochementError):
            generer_code_lettrage(-1)


class TestSoldeRapprochement(unittest.TestCase):
    def test_calcul_du_taux(self):
        releve = [
            LigneReleve("r1", date(2026, 7, 4), "A", Decimal("-100")),
            LigneReleve("r2", date(2026, 7, 4), "B", Decimal("-999")),
        ]
        ecritures = [LigneEcritureBanque("e1", date(2026, 7, 4), "A", debit=Decimal("0"), credit=Decimal("100"))]
        resultats = proposer_rapprochements(releve, ecritures)
        solde = calculer_solde_rapprochement(resultats)
        self.assertEqual(solde.nombre_lignes_releve, 2)
        self.assertEqual(solde.nombre_rapprochees, 1)
        self.assertEqual(solde.nombre_non_rapprochees, 1)
        self.assertAlmostEqual(solde.taux_rapprochement(), 0.5)

    def test_taux_100_pourcent_si_aucune_ligne(self):
        solde = calculer_solde_rapprochement([])
        self.assertEqual(solde.taux_rapprochement(), 1.0)


if __name__ == "__main__":
    unittest.main()
