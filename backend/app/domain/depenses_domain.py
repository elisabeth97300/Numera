"""
Logique métier pure pour "quelles dépenses puis-je réduire ?" : classe les
comptes de charge en "compressibles" (dépenses discrétionnaires, ajustables
à court terme) et "structurelles" (salaires, loyers, engagements longs) par
une nomenclature simple basée sur le préfixe de compte PCG, puis classe les
compressibles par montant décroissant.

Cette catégorisation est un point de départ, pas une vérité absolue : un
compte "compressible" pour une entreprise peut être stratégique pour une
autre (ex: 623 publicité pour une entreprise en phase d'acquisition clients).
Le comptable garde la main pour nuancer.
"""

from dataclasses import dataclass
from decimal import Decimal

# Préfixe de compte PCG -> (libellé, compressible ?)
NOMENCLATURE_CHARGES = {
    "6135": ("Locations mobilières", True),
    "6132": ("Locations immobilières", False),
    "6226": ("Honoraires", True),
    "6234": ("Cadeaux clientèle", True),
    "6256": ("Missions et réceptions", True),
    "6257": ("Réceptions", True),
    "6182": ("Documentation", True),
    "6183": ("Formation", True),
    "6231": ("Publicité, annonces", True),
    "6247": ("Transports de personnel", True),
    "626": ("Frais postaux et télécommunications", True),
    "641": ("Rémunérations du personnel", False),
    "645": ("Charges de sécurité sociale", False),
    "681": ("Dotations aux amortissements", False),
    "661": ("Charges d'intérêts", False),
}


@dataclass
class SuggestionReduction:
    compte_pcg: str
    libelle: str
    montant: Decimal


def _classifier(compte_pcg: str) -> tuple[str, bool] | None:
    for prefixe, (libelle, compressible) in sorted(NOMENCLATURE_CHARGES.items(), key=lambda x: -len(x[0])):
        if compte_pcg.startswith(prefixe):
            return libelle, compressible
    return None


def identifier_depenses_reductibles(comptes_charges: dict[str, Decimal]) -> list[SuggestionReduction]:
    """
    `comptes_charges` : {compte_pcg: montant} sur la période analysée.
    Retourne les postes compressibles connus, triés par montant décroissant —
    les meilleurs candidats à une réduction rapide en tête de liste.
    """
    suggestions = []
    for compte_pcg, montant in comptes_charges.items():
        if montant <= 0:
            continue
        classification = _classifier(compte_pcg)
        if classification is None:
            continue
        libelle, compressible = classification
        if compressible:
            suggestions.append(SuggestionReduction(compte_pcg, libelle, montant))

    return sorted(suggestions, key=lambda s: s.montant, reverse=True)
