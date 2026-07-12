import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.document_domain import (  # noqa: E402
    ChampExtrait,
    DocumentError,
    ResultatOCR,
    TypeDocument,
    calculer_hash,
    necessite_relecture_manuelle,
    valider_fichier,
)


class TestValidationFichier(unittest.TestCase):
    def test_extension_valide_acceptee(self):
        valider_fichier("facture.pdf", 1024, TypeDocument.FACTURE_ACHAT)  # ne doit pas lever

    def test_extension_invalide_refusee(self):
        with self.assertRaises(DocumentError):
            valider_fichier("facture.exe", 1024, TypeDocument.FACTURE_ACHAT)

    def test_fichier_vide_refuse(self):
        with self.assertRaises(DocumentError):
            valider_fichier("facture.pdf", 0, TypeDocument.FACTURE_ACHAT)

    def test_fichier_trop_gros_refuse(self):
        with self.assertRaises(DocumentError):
            valider_fichier("facture.pdf", 50 * 1024 * 1024, TypeDocument.FACTURE_ACHAT)

    def test_fec_accepte_txt_et_csv(self):
        valider_fichier("export.txt", 2048, TypeDocument.FEC)
        valider_fichier("export.csv", 2048, TypeDocument.FEC)


class TestHash(unittest.TestCase):
    def test_meme_contenu_donne_meme_hash(self):
        contenu = b"facture EDF 184.20 euros"
        self.assertEqual(calculer_hash(contenu), calculer_hash(contenu))

    def test_contenu_different_donne_hash_different(self):
        self.assertNotEqual(calculer_hash(b"facture A"), calculer_hash(b"facture B"))


class TestResultatOCR(unittest.TestCase):
    def test_confiance_globale_moyenne_des_champs(self):
        resultat = ResultatOCR(
            texte_brut="...",
            champs=[
                ChampExtrait("montant_ttc", "221.04", 0.95),
                ChampExtrait("date", "04/07/2026", 0.60),
            ],
        )
        self.assertAlmostEqual(resultat.confiance_globale(), 0.775)

    def test_confiance_globale_zero_si_aucun_champ(self):
        resultat = ResultatOCR(texte_brut="illisible")
        self.assertEqual(resultat.confiance_globale(), 0.0)

    def test_champs_a_verifier_filtre_sous_le_seuil(self):
        resultat = ResultatOCR(
            texte_brut="...",
            champs=[
                ChampExtrait("montant_ttc", "221.04", 0.95),
                ChampExtrait("tiers", "EDF", 0.40),
            ],
        )
        a_verifier = resultat.champs_a_verifier(seuil=0.7)
        self.assertEqual([c.nom for c in a_verifier], ["tiers"])

    def test_necessite_relecture_si_aucun_champ(self):
        self.assertTrue(necessite_relecture_manuelle(ResultatOCR(texte_brut="")))

    def test_necessite_relecture_si_confiance_faible(self):
        resultat = ResultatOCR(texte_brut="...", champs=[ChampExtrait("montant", "?", 0.3)])
        self.assertTrue(necessite_relecture_manuelle(resultat))

    def test_pas_de_relecture_si_confiance_haute(self):
        resultat = ResultatOCR(texte_brut="...", champs=[ChampExtrait("montant", "221.04", 0.9)])
        self.assertFalse(necessite_relecture_manuelle(resultat))


if __name__ == "__main__":
    unittest.main()
