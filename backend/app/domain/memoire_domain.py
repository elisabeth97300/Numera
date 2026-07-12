"""
Moteur de mémoire / apprentissage des habitudes comptables.

Principe : chaque fois qu'un comptable valide une proposition (avec ou sans
correction), on enregistre l'association (tiers normalisé -> compte PCG
retenu) pour ce client. La fois suivante que ce tiers apparaît, si
l'historique est suffisamment consistant, on peut proposer ce compte avec un
niveau de confiance élevé — sans même solliciter le LLM sur ce point précis.

C'est un apprentissage simple (comptage de fréquence), pas un modèle
statistique complexe : suffisant pour capturer "cette entreprise met toujours
Amazon en 606300", qui est le cas d'usage réel décrit.
"""

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal


class MemoireError(Exception):
    pass


def normaliser_tiers(tiers: str) -> str:
    """
    Normalise un nom de tiers pour le matching : minuscules, sans accents,
    sans ponctuation ni suffixes juridiques courants (SARL, SAS...), espaces
    compressés. 'Amazon EU Sarl' et 'AMAZON EU SARL' doivent matcher.
    """
    texte = unicodedata.normalize("NFKD", tiers).encode("ascii", "ignore").decode("ascii")
    texte = texte.lower().strip()
    texte = re.sub(r"\b(sarl|sas|sasu|sa|eurl|sci|ei)\b", "", texte)
    texte = re.sub(r"[^\w\s]", " ", texte)
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte


@dataclass
class HistoriqueTiers:
    """Vue agrégée de l'historique de comptabilisation d'un tiers pour un client."""

    tiers_normalise: str
    compte_pcg: str
    nombre_confirmations: int


SEUIL_CONFIANCE_HAUTE = 3  # nombre de confirmations à partir duquel on considère l'habitude fiable
SEUIL_CONFIANCE_MOYENNE = 1


@dataclass
class SuggestionMemoire:
    compte_pcg: str
    confiance: float
    nombre_confirmations: int


def suggerer_depuis_memoire(
    tiers: str, historiques: list[HistoriqueTiers]
) -> SuggestionMemoire | None:
    """
    Cherche si ce tiers a déjà été comptabilisé pour ce client. S'il existe
    plusieurs comptes différents dans l'historique (le tiers a été
    comptabilisé de façons différentes), on retient le plus fréquent mais
    avec une confiance réduite — l'habitude n'est pas fiable si elle n'est
    pas cohérente.
    """
    tiers_normalise = normaliser_tiers(tiers)
    candidats = [h for h in historiques if h.tiers_normalise == tiers_normalise]
    if not candidats:
        return None

    candidats.sort(key=lambda h: h.nombre_confirmations, reverse=True)
    meilleur = candidats[0]

    if len(candidats) > 1:
        # plusieurs comptes différents utilisés pour ce même tiers -> confiance réduite
        total = sum(h.nombre_confirmations for h in candidats)
        confiance = 0.5 * (meilleur.nombre_confirmations / total)
    elif meilleur.nombre_confirmations >= SEUIL_CONFIANCE_HAUTE:
        confiance = 0.95
    elif meilleur.nombre_confirmations >= SEUIL_CONFIANCE_MOYENNE:
        confiance = 0.6
    else:
        confiance = 0.3

    return SuggestionMemoire(
        compte_pcg=meilleur.compte_pcg, confiance=confiance, nombre_confirmations=meilleur.nombre_confirmations
    )


# --- Moteur de confiance unifié -------------------------------------------
# Combine la confiance de plusieurs sources (OCR, LLM, mémoire) en une seule
# décision exploitable par l'interface de validation.

@dataclass
class DecisionConfiance:
    confiance_finale: float
    source_principale: str
    peut_auto_valider: bool  # réservé aux cas où la mémoire est quasi certaine ET l'IA d'accord


SEUIL_AUTO_VALIDATION = 0.9


def combiner_confiance(
    confiance_ocr: float,
    confiance_llm: float,
    suggestion_memoire: SuggestionMemoire | None,
    compte_propose_llm: str,
) -> DecisionConfiance:
    """
    Règle de combinaison :
    - si la mémoire est très confiante ET propose le MÊME compte que le LLM
      -> confiance finale élevée, éligible à l'auto-validation (mais reste
      un réglage produit à activer explicitement, jamais un défaut silencieux) ;
    - si la mémoire est confiante mais propose un compte DIFFÉRENT du LLM
      -> conflit signalé, confiance abaissée pour forcer une vérification ;
    - sinon, confiance finale = moyenne pondérée OCR/LLM (la mémoire n'a pas
      d'avis assez fort pour peser dans la décision).
    """
    if suggestion_memoire is not None and suggestion_memoire.confiance >= 0.9:
        if suggestion_memoire.compte_pcg == compte_propose_llm:
            confiance_finale = max(suggestion_memoire.confiance, confiance_llm)
            return DecisionConfiance(
                confiance_finale=confiance_finale,
                source_principale="memoire+llm_accord",
                peut_auto_valider=confiance_finale >= SEUIL_AUTO_VALIDATION and confiance_ocr >= 0.7,
            )
        else:
            return DecisionConfiance(
                confiance_finale=min(confiance_llm, 0.4),
                source_principale="conflit_memoire_llm",
                peut_auto_valider=False,
            )

    confiance_finale = 0.4 * confiance_ocr + 0.6 * confiance_llm
    return DecisionConfiance(confiance_finale=confiance_finale, source_principale="ocr_llm", peut_auto_valider=False)
