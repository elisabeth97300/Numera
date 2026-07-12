"""
Logique métier pure du module IA Comptable.

Cette couche ne fait AUCUN appel au LLM (ça reste dans
app/services/ia_comptable_service.py, qui a besoin du réseau). Elle prend en
entrée ce que le LLM a répondu (déjà parsé en structure Python) et applique
les règles qui garantissent que le produit reste un copilote, jamais un
pilote automatique :
- une proposition dont le compte PCG est mal formé n'est jamais présentée
  comme fiable ;
- HT + TVA doit être cohérent avec TTC, sinon la proposition est signalée ;
- un score de confiance bas fait passer la proposition en "à vérifier en
  priorité" plutôt que d'être validée en un clic.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class StatutProposition(str, Enum):
    EN_ATTENTE = "en_attente"
    VALIDEE = "validee"
    MODIFIEE = "modifiee"
    REJETEE = "rejetee"


class PropositionError(Exception):
    """Erreur métier liée à une proposition d'écriture générée par l'IA."""


RE_COMPTE_PCG = re.compile(r"^\d{6,8}$")

# Tolérance d'arrondi : les factures réelles ont parfois 1 centime d'écart
# entre HT+TVA affiché et TTC affiché (arrondis en cascade côté fournisseur).
# Au-delà, on ne fait pas confiance à la proposition sans vérification.
TOLERANCE_ARRONDI = Decimal("0.02")


def valider_format_compte_pcg(compte: str) -> None:
    """Un compte du Plan Comptable Général français a entre 6 et 8 chiffres."""
    if not RE_COMPTE_PCG.match(compte):
        raise PropositionError(f"'{compte}' n'est pas un format de compte PCG valide")


@dataclass
class PropositionBrute:
    """Ce que le LLM a proposé, avant validation métier."""

    compte_pcg: str
    tiers: str
    montant_ht: Decimal
    montant_tva: Decimal
    taux_tva: Decimal
    score_confiance: float


@dataclass
class PropositionValidee:
    compte_pcg: str
    tiers: str
    montant_ht: Decimal
    montant_tva: Decimal
    montant_ttc: Decimal
    taux_tva: Decimal
    score_confiance: float
    a_verifier_en_priorite: bool
    avertissements: list[str]


SEUIL_CONFIANCE_FIABLE = 0.75


def valider_proposition(brute: PropositionBrute, montant_ttc_attendu: Decimal | None = None) -> PropositionValidee:
    """
    Applique les contrôles de cohérence sur une proposition brute issue du
    LLM. Ne lève une erreur bloquante que si le compte PCG est structurellement
    invalide (impossible à présenter tel quel) ; les autres incohérences
    (montants, confiance basse) ne bloquent pas la proposition mais la
    marquent comme prioritaire à vérifier, pour laisser le comptable trancher.
    """
    valider_format_compte_pcg(brute.compte_pcg)  # lève PropositionError si invalide

    avertissements: list[str] = []
    montant_ttc_calcule = brute.montant_ht + brute.montant_tva

    if montant_ttc_attendu is not None:
        ecart = abs(montant_ttc_calcule - montant_ttc_attendu)
        if ecart > TOLERANCE_ARRONDI:
            avertissements.append(
                f"HT + TVA ({montant_ttc_calcule}) ne correspond pas au TTC lu sur le document "
                f"({montant_ttc_attendu}), écart de {ecart}"
            )

    if brute.montant_ht < 0 or brute.montant_tva < 0:
        avertissements.append("Montant négatif proposé — probablement un avoir, à vérifier")

    taux_theoriques = {Decimal("0"), Decimal("2.1"), Decimal("5.5"), Decimal("10"), Decimal("20")}
    if brute.taux_tva not in taux_theoriques:
        avertissements.append(f"Taux de TVA {brute.taux_tva}% inhabituel en France")

    a_verifier = brute.score_confiance < SEUIL_CONFIANCE_FIABLE or len(avertissements) > 0

    return PropositionValidee(
        compte_pcg=brute.compte_pcg,
        tiers=brute.tiers,
        montant_ht=brute.montant_ht,
        montant_tva=brute.montant_tva,
        montant_ttc=montant_ttc_calcule,
        taux_tva=brute.taux_tva,
        score_confiance=brute.score_confiance,
        a_verifier_en_priorite=a_verifier,
        avertissements=avertissements,
    )


def peut_etre_validee_directement(proposition: PropositionValidee) -> bool:
    """Utilisé côté UI pour distinguer un bouton 'Valider' simple d'un bouton qui force une relecture."""
    return not proposition.a_verifier_en_priorite
