import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.proposition_domain import (  # noqa: E402
    PropositionBrute,
    PropositionError,
    peut_etre_validee_directement,
    valider_format_compte_pcg,
    valider_proposition,
)


class TestFormatComptePCG(unittest.TestCase):
    def test_compte_six_chiffres_valide(self):
        valider_format_compte_pcg("606100")

    def test_compte_avec_lettres_refuse(self):
        with self.assertRaises(PropositionError):
            valider_format_compte_pcg("60610A")

    def test_compte_trop_court_refuse(self):
        with self.assertRaises(PropositionError):
            valider_format_compte_pcg("606")


class TestValiderProposition(unittest.TestCase):
    def test_proposition_coherente_et_confiante_ne_necessite_pas_verification(self):
        brute = PropositionBrute(
            compte_pcg="606100",
            tiers="EDF",
            montant_ht=Decimal("184.20"),
            montant_tva=Decimal("36.84"),
            taux_tva=Decimal("20"),
            score_confiance=0.92,
        )
        validee = valider_proposition(brute, montant_ttc_attendu=Decimal("221.04"))
        self.assertFalse(validee.a_verifier_en_priorite)
        self.assertEqual(validee.avertissements, [])
        self.assertTrue(peut_etre_validee_directement(validee))

    def test_ecart_ttc_signale_comme_a_verifier(self):
        brute = PropositionBrute(
            compte_pcg="606100",
            tiers="EDF",
            montant_ht=Decimal("184.20"),
            montant_tva=Decimal("36.84"),
            taux_tva=Decimal("20"),
            score_confiance=0.9,
        )
        validee = valider_proposition(brute, montant_ttc_attendu=Decimal("300.00"))
        self.assertTrue(validee.a_verifier_en_priorite)
        self.assertTrue(any("TTC" in a for a in validee.avertissements))

    def test_petit_ecart_arrondi_tolere(self):
        brute = PropositionBrute(
            compte_pcg="606100",
            tiers="EDF",
            montant_ht=Decimal("184.20"),
            montant_tva=Decimal("36.85"),  # 1 centime d'écart avec le TTC attendu
            taux_tva=Decimal("20"),
            score_confiance=0.9,
        )
        validee = valider_proposition(brute, montant_ttc_attendu=Decimal("221.04"))
        self.assertFalse(validee.a_verifier_en_priorite)

    def test_confiance_basse_force_verification_meme_sans_incoherence(self):
        brute = PropositionBrute(
            compte_pcg="606100",
            tiers="EDF",
            montant_ht=Decimal("184.20"),
            montant_tva=Decimal("36.84"),
            taux_tva=Decimal("20"),
            score_confiance=0.4,
        )
        validee = valider_proposition(brute, montant_ttc_attendu=Decimal("221.04"))
        self.assertTrue(validee.a_verifier_en_priorite)
        self.assertFalse(peut_etre_validee_directement(validee))

    def test_taux_tva_inhabituel_signale(self):
        brute = PropositionBrute(
            compte_pcg="606100",
            tiers="EDF",
            montant_ht=Decimal("100"),
            montant_tva=Decimal("15"),
            taux_tva=Decimal("15"),  # n'existe pas en France
            score_confiance=0.9,
        )
        validee = valider_proposition(brute)
        self.assertTrue(any("inhabituel" in a for a in validee.avertissements))

    def test_compte_invalide_leve_une_erreur_bloquante(self):
        brute = PropositionBrute(
            compte_pcg="ABC",
            tiers="EDF",
            montant_ht=Decimal("100"),
            montant_tva=Decimal("20"),
            taux_tva=Decimal("20"),
            score_confiance=0.9,
        )
        with self.assertRaises(PropositionError):
            valider_proposition(brute)


if __name__ == "__main__":
    unittest.main()
