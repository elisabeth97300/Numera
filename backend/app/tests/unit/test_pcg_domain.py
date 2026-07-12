import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from domain.pcg_domain import (  # noqa: E402
    PCGError,
    compte_existe,
    lister_classe,
    obtenir_compte,
    rechercher_comptes,
    suggerer_comptes_proches,
)


class TestCompteExiste(unittest.TestCase):
    def test_compte_connu(self):
        self.assertTrue(compte_existe("606100"))

    def test_compte_inconnu(self):
        self.assertFalse(compte_existe("999999"))


class TestObtenirCompte(unittest.TestCase):
    def test_compte_valide_retourne_info_complete(self):
        info = obtenir_compte("512000")
        self.assertEqual(info.classe, 5)
        self.assertEqual(info.libelle_classe, "Comptes financiers")

    def test_compte_invalide_leve_erreur(self):
        with self.assertRaises(PCGError):
            obtenir_compte("999999")


class TestRechercherComptes(unittest.TestCase):
    def test_recherche_par_prefixe_numerique(self):
        resultats = rechercher_comptes("445")
        self.assertTrue(all(c.compte_pcg.startswith("445") for c in resultats))
        self.assertGreater(len(resultats), 3)

    def test_recherche_par_mot_cle(self):
        resultats = rechercher_comptes("assurance")
        self.assertTrue(any(c.compte_pcg == "616000" for c in resultats))

    def test_recherche_limite_le_nombre_de_resultats(self):
        resultats = rechercher_comptes("6", limite=2)
        self.assertEqual(len(resultats), 2)


class TestSuggererComptesProches(unittest.TestCase):
    def test_compte_proche_suggere_via_prefixe(self):
        suggestions = suggerer_comptes_proches("606305")
        self.assertTrue(any(s.compte_pcg == "606300" for s in suggestions))

    def test_aucun_compte_proche_retourne_liste_vide(self):
        self.assertEqual(suggerer_comptes_proches("999999"), [])


class TestListerClasse(unittest.TestCase):
    def test_classe_valide(self):
        comptes = lister_classe(6)
        self.assertTrue(all(c.classe == 6 for c in comptes))
        self.assertGreater(len(comptes), 10)

    def test_classe_invalide_leve_erreur(self):
        with self.assertRaises(PCGError):
            lister_classe(9)


if __name__ == "__main__":
    unittest.main()
