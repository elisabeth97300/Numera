"""
Prévisions étendues : TVA à venir, impôt sur les sociétés estimé, et
simulation d'impact d'une embauche ou d'un investissement sur la trésorerie
projetée. Réutilise tresorerie_domain.ProjectionTresorerie comme base.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.tresorerie_domain import MouvementJournalier, ProjectionTresorerie, projeter_tresorerie


class PrevisionError(Exception):
    pass


def prevoir_prochaine_tva(historique_soldes: list[Decimal]) -> Decimal:
    """
    Moyenne mobile simple des derniers soldes de TVA à payer connus. Une
    vraie prévision tiendrait compte de la saisonnalité (ex: TVA plus élevée
    en fin d'année pour une activité de vente au détail) — amélioration
    naturelle une fois plusieurs exercices d'historique disponibles.
    """
    if not historique_soldes:
        raise PrevisionError("Historique de TVA insuffisant pour prévoir")
    return sum(historique_soldes, Decimal("0")) / len(historique_soldes)


# Barème IS français PME 2026 (simplifié) : taux réduit 15% jusqu'à 42 500 €
# de bénéfice, 25% au-delà (sous réserve des conditions d'éligibilité au taux
# réduit — capital détenu à 75% par des personnes physiques, CA < 10M€, à
# vérifier au cas par cas, jamais appliqué automatiquement sans confirmation).
SEUIL_TAUX_REDUIT_IS = Decimal("42500")
TAUX_REDUIT_IS = Decimal("0.15")
TAUX_NORMAL_IS = Decimal("0.25")


def estimer_is(resultat_fiscal: Decimal, eligible_taux_reduit: bool = True) -> Decimal:
    """
    Estimation indicative de l'IS dû, PAS une déclaration fiscale. À faire
    valider par l'expert-comptable avant toute communication au dirigeant
    comme un montant définitif — le résultat fiscal diffère souvent du
    résultat comptable (réintégrations, déductions) que ce calcul ignore.
    """
    if resultat_fiscal <= 0:
        return Decimal("0")

    if not eligible_taux_reduit:
        return resultat_fiscal * TAUX_NORMAL_IS

    if resultat_fiscal <= SEUIL_TAUX_REDUIT_IS:
        return resultat_fiscal * TAUX_REDUIT_IS

    return SEUIL_TAUX_REDUIT_IS * TAUX_REDUIT_IS + (resultat_fiscal - SEUIL_TAUX_REDUIT_IS) * TAUX_NORMAL_IS


def simuler_charge_recurrente(
    projection_de_base: ProjectionTresorerie, mouvements_historiques: list[MouvementJournalier], cout_mensuel: Decimal
) -> ProjectionTresorerie:
    """
    Simule l'impact d'une nouvelle charge récurrente (embauche : salaire +
    charges patronales mensualisés) sur la projection de trésorerie, en
    ajoutant le coût journalier équivalent à chaque mouvement historique
    avant de reprojeter — plutôt que de bricoler le résultat final, on
    perturbe l'entrée et on refait tourner la même fonction de projection,
    ce qui garantit que la cohérence (moyenne, optimiste, pessimiste) reste
    respectée.
    """
    cout_journalier = cout_mensuel / Decimal("30")
    mouvements_simules = [
        MouvementJournalier(date=m.date, montant_net=m.montant_net - cout_journalier) for m in mouvements_historiques
    ]
    return projeter_tresorerie(projection_de_base.solde_actuel, mouvements_simules, projection_de_base.horizon_jours)


def simuler_investissement_ponctuel(
    projection_de_base: ProjectionTresorerie, montant: Decimal
) -> ProjectionTresorerie:
    """
    Simule une sortie de trésorerie unique (achat d'équipement, par exemple)
    dès aujourd'hui : impacte directement le solde de départ de la
    projection, sans toucher au rythme des mouvements récurrents.
    """
    if montant <= 0:
        raise PrevisionError("Le montant d'un investissement simulé doit être positif")

    return ProjectionTresorerie(
        solde_actuel=projection_de_base.solde_actuel - montant,
        horizon_jours=projection_de_base.horizon_jours,
        solde_projete=projection_de_base.solde_projete - montant,
        scenario_optimiste=projection_de_base.scenario_optimiste - montant,
        scenario_pessimiste=projection_de_base.scenario_pessimiste - montant,
        moyenne_mouvement_journalier=projection_de_base.moyenne_mouvement_journalier,
        nombre_jours_historique=projection_de_base.nombre_jours_historique,
    )
