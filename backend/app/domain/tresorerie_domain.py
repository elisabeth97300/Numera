"""
Logique métier pure de projection de trésorerie.

Méthode volontairement simple pour un MVP : projection linéaire à partir du
mouvement net moyen observé sur l'historique récent, avec un scénario
optimiste (meilleure période observée) et pessimiste (pire période observée)
pour donner une fourchette plutôt qu'un faux-semblant de précision. Une vraie
prévision de trésorerie tiendrait aussi compte des échéances connues
(factures fournisseurs à échéance, salaires à date fixe) — amélioration
naturelle une fois ce module validé avec un cabinet pilote.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class TresorerieError(Exception):
    pass


@dataclass
class MouvementJournalier:
    date: date
    montant_net: Decimal  # positif = encaissement net du jour, négatif = décaissement net


@dataclass
class ProjectionTresorerie:
    solde_actuel: Decimal
    horizon_jours: int
    solde_projete: Decimal
    scenario_optimiste: Decimal
    scenario_pessimiste: Decimal
    moyenne_mouvement_journalier: Decimal
    nombre_jours_historique: int

    def risque_decouvert(self) -> bool:
        """Le scénario pessimiste passe-t-il en négatif ? C'est ce qui doit déclencher une alerte."""
        return self.scenario_pessimiste < 0


def projeter_tresorerie(
    solde_actuel: Decimal, mouvements: list[MouvementJournalier], horizon_jours: int
) -> ProjectionTresorerie:
    if horizon_jours <= 0:
        raise TresorerieError("L'horizon de projection doit être positif")
    if not mouvements:
        raise TresorerieError("Historique de mouvements insuffisant pour projeter la trésorerie")

    moyenne = sum((m.montant_net for m in mouvements), Decimal("0")) / len(mouvements)
    meilleur = max(m.montant_net for m in mouvements)
    pire = min(m.montant_net for m in mouvements)

    return ProjectionTresorerie(
        solde_actuel=solde_actuel,
        horizon_jours=horizon_jours,
        solde_projete=solde_actuel + moyenne * horizon_jours,
        scenario_optimiste=solde_actuel + meilleur * horizon_jours,
        scenario_pessimiste=solde_actuel + pire * horizon_jours,
        moyenne_mouvement_journalier=moyenne,
        nombre_jours_historique=len(mouvements),
    )
