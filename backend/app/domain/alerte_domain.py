"""
Génération d'alertes : agrège les signaux des autres modules (trésorerie,
anomalies, TVA, échéances d'exercice) en une liste priorisée. Ce module ne
recalcule rien lui-même — il compose des résultats déjà produits par
tresorerie_domain, anomaly_domain, tva_domain, exercice_domain — pour rester
simple à faire évoluer si de nouvelles sources d'alerte apparaissent.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class NiveauAlerte(str, Enum):
    INFO = "info"
    ATTENTION = "attention"
    URGENT = "urgent"


@dataclass
class Alerte:
    niveau: NiveauAlerte
    message: str


def alerte_risque_tresorerie(scenario_pessimiste: Decimal, horizon_jours: int) -> Alerte | None:
    if scenario_pessimiste < 0:
        return Alerte(
            NiveauAlerte.URGENT,
            f"Risque de découvert d'ici {horizon_jours} jours dans le scénario le plus défavorable "
            f"(solde projeté : {scenario_pessimiste} €)",
        )
    return None


def alerte_anomalies(nombre_anomalies: int) -> Alerte | None:
    if nombre_anomalies == 0:
        return None
    niveau = NiveauAlerte.ATTENTION if nombre_anomalies < 5 else NiveauAlerte.URGENT
    return Alerte(niveau, f"{nombre_anomalies} anomalie(s) détectée(s) à vérifier")


def alerte_tva_a_payer(solde_a_payer: Decimal, date_echeance: date, date_du_jour: date) -> Alerte | None:
    if solde_a_payer <= 0:
        return None
    jours_restants = (date_echeance - date_du_jour).days
    if jours_restants < 0:
        return Alerte(NiveauAlerte.URGENT, f"TVA de {solde_a_payer} € en retard de paiement")
    if jours_restants <= 7:
        return Alerte(
            NiveauAlerte.ATTENTION, f"TVA de {solde_a_payer} € à payer dans {jours_restants} jour(s)"
        )
    return None


def alerte_exercice_proche_cloture(date_fin_exercice: date, date_du_jour: date, statut: str) -> Alerte | None:
    if statut != "en_cours":
        return None
    jours_restants = (date_fin_exercice - date_du_jour).days
    if 0 <= jours_restants <= 30:
        return Alerte(NiveauAlerte.INFO, f"L'exercice se termine dans {jours_restants} jour(s) — penser à préparer la clôture")
    return None


def prioriser_alertes(alertes: list[Alerte | None]) -> list[Alerte]:
    """Filtre les None puis trie par niveau de gravité décroissant (urgent en premier)."""
    ordre = {NiveauAlerte.URGENT: 0, NiveauAlerte.ATTENTION: 1, NiveauAlerte.INFO: 2}
    valides = [a for a in alertes if a is not None]
    return sorted(valides, key=lambda a: ordre[a.niveau])
