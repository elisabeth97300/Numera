"""
Logique métier pure du module Import & OCR.
Aucune dépendance à un framework, à S3 ou à un moteur OCR — juste les règles :
quels fichiers sont acceptés, comment on identifie un doublon exact, et
comment on interprète le résultat brut d'un OCR (score de confiance par champ).
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class TypeDocument(str, Enum):
    FACTURE_ACHAT = "facture_achat"
    FACTURE_VENTE = "facture_vente"
    RELEVE_BANCAIRE = "releve_bancaire"
    FEC = "fec"
    AUTRE = "autre"


class StatutOCR(str, Enum):
    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ERREUR = "erreur"


class DocumentError(Exception):
    """Erreur métier liée à l'import ou au traitement d'un document."""


EXTENSIONS_ACCEPTEES = {
    TypeDocument.FACTURE_ACHAT: {".pdf", ".png", ".jpg", ".jpeg"},
    TypeDocument.FACTURE_VENTE: {".pdf", ".png", ".jpg", ".jpeg"},
    TypeDocument.RELEVE_BANCAIRE: {".pdf", ".csv", ".xlsx"},
    TypeDocument.FEC: {".txt", ".csv"},
    TypeDocument.AUTRE: {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".xlsx", ".txt"},
}

TAILLE_MAX_OCTETS = 20 * 1024 * 1024  # 20 Mo — au-delà, probablement pas une simple facture


def valider_fichier(nom_fichier: str, taille_octets: int, type_document: TypeDocument) -> None:
    """Rejette un fichier avant même de le stocker si son extension ou sa taille n'a pas de sens."""
    if taille_octets <= 0:
        raise DocumentError("Fichier vide")
    if taille_octets > TAILLE_MAX_OCTETS:
        raise DocumentError(f"Fichier trop volumineux (max {TAILLE_MAX_OCTETS // (1024*1024)} Mo)")

    extension = "." + nom_fichier.rsplit(".", 1)[-1].lower() if "." in nom_fichier else ""
    autorisees = EXTENSIONS_ACCEPTEES.get(type_document, EXTENSIONS_ACCEPTEES[TypeDocument.AUTRE])
    if extension not in autorisees:
        raise DocumentError(
            f"Extension '{extension}' non supportée pour un document de type {type_document.value} "
            f"(attendu : {', '.join(sorted(autorisees))})"
        )


def calculer_hash(contenu_binaire: bytes) -> str:
    """Empreinte SHA-256 du contenu exact du fichier, utilisée pour la détection de doublon exact."""
    return hashlib.sha256(contenu_binaire).hexdigest()


@dataclass
class ChampExtrait:
    """Un champ extrait par l'OCR, avec son score de confiance individuel (0 à 1)."""

    nom: str
    valeur: str
    confiance: float


@dataclass
class ResultatOCR:
    texte_brut: str
    champs: list[ChampExtrait] = field(default_factory=list)

    def confiance_globale(self) -> float:
        """Moyenne des scores de confiance ; 0 si aucun champ n'a été extrait (échec probable)."""
        if not self.champs:
            return 0.0
        return sum(c.confiance for c in self.champs) / len(self.champs)

    def champs_a_verifier(self, seuil: float = 0.7) -> list[ChampExtrait]:
        """
        Champs dont la confiance est en dessous du seuil : ce sont ceux que
        l'interface doit mettre en évidence pour que le comptable les
        vérifie en priorité, plutôt que de tout revérifier ligne par ligne.
        """
        return [c for c in self.champs if c.confiance < seuil]


def necessite_relecture_manuelle(resultat: ResultatOCR, seuil_global: float = 0.6) -> bool:
    """
    Décide si le document doit être signalé comme "à relire" avant même de
    proposer une écriture — évite de faire perdre du temps au comptable avec
    une proposition IA construite sur une lecture OCR trop incertaine.
    """
    return resultat.confiance_globale() < seuil_global or len(resultat.champs) == 0
