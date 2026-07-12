"""
Logique métier pure de gestion des exercices comptables et de la reprise de dossier.

Ce module ne dépend d'aucun framework (pas de SQLAlchemy, pas de FastAPI) : il ne
manipule que des objets Python simples (dataclasses). Objectif :
- pouvoir tester exhaustivement les règles comptables (équilibre, report des
  soldes, verrouillage) sans base de données ni serveur ;
- garantir que la logique la plus sensible du produit — celle qui touche à des
  obligations légales (intangibilité des exercices clôturés, art. L123-22 du
  Code de commerce) — est fiable indépendamment de la techno utilisée pour la
  persister.

La couche API/SQLAlchemy (voir app/models et app/api) ne fait qu'orchestrer ces
fonctions : elle charge des objets depuis la base, appelle ces fonctions, puis
persiste le résultat. Toute la décision métier est ici.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional


class StatutExercice(str, Enum):
    NON_DEMARRE = "non_demarre"
    EN_COURS = "en_cours"
    CLOTURE = "cloture"
    ARCHIVE = "archive"


class OrigineExercice(str, Enum):
    NOUVEAU = "nouveau"
    REPRIS = "repris"


class SourceSolde(str, Enum):
    SAISIE_MANUELLE = "saisie_manuelle"
    IMPORT_FEC = "import_fec"
    CLOTURE_AUTO = "cloture_auto"


class ExerciceError(Exception):
    """Erreur métier liée à la gestion d'un exercice comptable."""


@dataclass
class LigneSolde:
    """Une ligne du bilan d'ouverture (ou de clôture) : un compte PCG et son solde."""

    compte_pcg: str
    solde_debit: Decimal = Decimal("0")
    solde_credit: Decimal = Decimal("0")
    source: SourceSolde = SourceSolde.SAISIE_MANUELLE

    def classe(self) -> int:
        """Première position du compte PCG = classe comptable (1 à 8)."""
        return int(self.compte_pcg[0])

    def est_compte_de_bilan(self) -> bool:
        return self.classe() in (1, 2, 3, 4, 5)

    def est_compte_de_gestion(self) -> bool:
        return self.classe() in (6, 7)


@dataclass
class BalanceCompte:
    """Cumul débit/crédit d'un compte sur un exercice, tel que sorti de la balance."""

    compte_pcg: str
    total_debit: Decimal
    total_credit: Decimal

    def solde(self) -> Decimal:
        """Positif = solde débiteur, négatif = solde créditeur."""
        return self.total_debit - self.total_credit


@dataclass
class Exercice:
    id: str
    client_id: str
    date_debut: date
    date_fin: date
    origine: OrigineExercice
    statut: StatutExercice = StatutExercice.NON_DEMARRE
    exercice_precedent_id: Optional[str] = None
    solde_ouverture: list[LigneSolde] = field(default_factory=list)


def valider_equilibre_solde_ouverture(lignes: list[LigneSolde]) -> None:
    """
    Un bilan de reprise doit être équilibré : total débit == total crédit.
    Sinon il ne peut pas servir de point de départ à un exercice.
    """
    total_debit = sum((l.solde_debit for l in lignes), Decimal("0"))
    total_credit = sum((l.solde_credit for l in lignes), Decimal("0"))
    if total_debit != total_credit:
        raise ExerciceError(
            f"Le solde d'ouverture n'est pas équilibré : "
            f"débit={total_debit} crédit={total_credit}"
        )


def demarrer_exercice(
    exercice: Exercice, solde_ouverture: Optional[list[LigneSolde]] = None
) -> Exercice:
    """
    Fait passer un exercice de NON_DEMARRE à EN_COURS.

    - Exercice `nouveau` : aucun solde d'ouverture requis (liste vide acceptée).
    - Exercice `repris` : un solde d'ouverture équilibré est obligatoire — c'est
      la traduction directe de la contrainte métier du client ("possible pour
      une nouvelle entreprise OU une ancienne avec des exercices déjà clôturés").
    """
    if exercice.statut != StatutExercice.NON_DEMARRE:
        raise ExerciceError(f"Impossible de démarrer un exercice au statut {exercice.statut}")

    if exercice.origine == OrigineExercice.REPRIS:
        if not solde_ouverture:
            raise ExerciceError(
                "Un exercice repris nécessite un solde d'ouverture "
                "(saisie manuelle ou import FEC de l'exercice précédent)"
            )
        valider_equilibre_solde_ouverture(solde_ouverture)
        exercice.solde_ouverture = solde_ouverture
    else:
        exercice.solde_ouverture = solde_ouverture or []

    exercice.statut = StatutExercice.EN_COURS
    return exercice


def verifier_ecriture_modifiable(exercice: Exercice) -> None:
    """
    Garde-fou central : à appeler avant tout INSERT/UPDATE/DELETE sur une ligne
    d'écriture. Lève une erreur métier si l'exercice est clôturé ou archivé.
    C'est cette fonction qui garantit l'intangibilité légale des exercices clos.
    """
    if exercice.statut == StatutExercice.CLOTURE:
        raise ExerciceError(
            "Exercice clôturé : les écritures sont verrouillées. "
            "Toute correction doit être passée sur l'exercice suivant."
        )
    if exercice.statut == StatutExercice.ARCHIVE:
        raise ExerciceError("Exercice archivé : lecture seule.")


def calculer_solde_ouverture_suivant(balance_finale: list[BalanceCompte]) -> list[LigneSolde]:
    """
    À partir de la balance finale d'un exercice clôturé, calcule le solde
    d'ouverture de l'exercice suivant :
    - comptes de bilan (classes 1 à 5) : reportés tels quels ;
    - comptes de gestion (classes 6 et 7) : jamais reportés, ils repartent à
      zéro sur le nouvel exercice (règle comptable de base) ;
    - le résultat net (produits - charges) est injecté en compte 120 "résultat
      de l'exercice (bénéfice)" si positif, ou 129 "résultat de l'exercice
      (perte)" si négatif.
    """
    lignes: list[LigneSolde] = []
    total_charges = Decimal("0")
    total_produits = Decimal("0")

    for compte in balance_finale:
        classe = int(compte.compte_pcg[0])
        if classe in (1, 2, 3, 4, 5):
            solde = compte.solde()
            if solde == 0:
                continue
            if solde > 0:
                lignes.append(
                    LigneSolde(compte.compte_pcg, solde_debit=solde, source=SourceSolde.CLOTURE_AUTO)
                )
            else:
                lignes.append(
                    LigneSolde(compte.compte_pcg, solde_credit=-solde, source=SourceSolde.CLOTURE_AUTO)
                )
        elif classe == 6:
            total_charges += compte.total_debit - compte.total_credit
        elif classe == 7:
            total_produits += compte.total_credit - compte.total_debit
        # classes 8 et suivantes (engagements hors bilan, etc.) : hors périmètre ici

    resultat = total_produits - total_charges
    if resultat > 0:
        lignes.append(LigneSolde("120000", solde_credit=resultat, source=SourceSolde.CLOTURE_AUTO))
    elif resultat < 0:
        lignes.append(LigneSolde("129000", solde_debit=-resultat, source=SourceSolde.CLOTURE_AUTO))

    return lignes


def cloturer_exercice(
    exercice: Exercice, balance_finale: list[BalanceCompte]
) -> tuple[Exercice, list[LigneSolde]]:
    """
    Clôture un exercice :
    1. revérifie que la balance finale est équilibrée (ceinture + bretelles, en
       plus de la contrainte déjà imposée écriture par écriture) ;
    2. verrouille l'exercice (statut -> CLOTURE) ;
    3. calcule le solde d'ouverture à transmettre à l'exercice suivant.

    Ne crée PAS l'exercice suivant : ça reste la responsabilité de la couche
    service/API, qui décide quand l'ouvrir.
    """
    if exercice.statut != StatutExercice.EN_COURS:
        raise ExerciceError(f"Impossible de clôturer un exercice au statut {exercice.statut}")

    total_debit = sum((c.total_debit for c in balance_finale), Decimal("0"))
    total_credit = sum((c.total_credit for c in balance_finale), Decimal("0"))
    if total_debit != total_credit:
        raise ExerciceError(
            f"La balance n'est pas équilibrée, clôture refusée : "
            f"débit={total_debit} crédit={total_credit}"
        )

    solde_suivant = calculer_solde_ouverture_suivant(balance_finale)
    exercice.statut = StatutExercice.CLOTURE
    return exercice, solde_suivant


def reouvrir_exercice(exercice: Exercice, role_utilisateur: str) -> Exercice:
    """
    Réouverture exceptionnelle d'un exercice clôturé, réservée aux admins
    (cas rare : correction avant liasse fiscale définitive).
    L'appelant (couche service) est responsable de tracer cet événement dans
    le module Audit — cette fonction ne fait que la vérification métier.
    """
    if role_utilisateur != "admin":
        raise ExerciceError("Seul un administrateur peut réouvrir un exercice clôturé")
    if exercice.statut != StatutExercice.CLOTURE:
        raise ExerciceError(f"Impossible de réouvrir un exercice au statut {exercice.statut}")
    exercice.statut = StatutExercice.EN_COURS
    return exercice
