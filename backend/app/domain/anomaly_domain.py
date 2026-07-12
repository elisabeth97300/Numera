"""
Logique métier pure de détection d'anomalies : doublons exacts (déjà couverts
par le hash de fichier dans document_domain.py) et doublons flous (même
montant, même tiers, dates proches — cas d'une facture scannée deux fois
sous des noms de fichiers différents), ainsi que quelques incohérences
simples (date hors exercice, TVA incohérente avec le taux légal).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum


class TypeAnomalie(str, Enum):
    DOUBLON_EXACT = "doublon_exact"
    DOUBLON_PROBABLE = "doublon_probable"
    DATE_HORS_EXERCICE = "date_hors_exercice"
    TAUX_TVA_INCONNU = "taux_tva_inconnu"


@dataclass
class EcritureComparable:
    """Vue simplifiée d'une écriture, suffisante pour détecter les doublons flous."""

    id: str
    tiers: str
    montant_ttc: Decimal
    date_ecriture: date


@dataclass
class Anomalie:
    type: TypeAnomalie
    message: str
    ecriture_id_1: str
    ecriture_id_2: str | None = None


TOLERANCE_JOURS_DOUBLON = 3
TOLERANCE_MONTANT_DOUBLON = Decimal("0.01")


def detecter_doublons_probables(ecritures: list[EcritureComparable]) -> list[Anomalie]:
    """
    Compare chaque paire d'écritures : même tiers (insensible à la casse),
    montant quasi identique, dates à quelques jours d'écart. Complexité O(n²)
    volontairement simple — suffisant pour le volume d'un cabinet (quelques
    milliers d'écritures par exercice et par client), à optimiser avec un
    index si le besoin réel se confirme plus tard.
    """
    anomalies: list[Anomalie] = []
    for i, a in enumerate(ecritures):
        for b in ecritures[i + 1 :]:
            if a.tiers.strip().lower() != b.tiers.strip().lower():
                continue
            if abs(a.montant_ttc - b.montant_ttc) > TOLERANCE_MONTANT_DOUBLON:
                continue
            if abs((a.date_ecriture - b.date_ecriture).days) > TOLERANCE_JOURS_DOUBLON:
                continue
            anomalies.append(
                Anomalie(
                    type=TypeAnomalie.DOUBLON_PROBABLE,
                    message=(
                        f"Deux écritures très proches pour '{a.tiers}' : "
                        f"{a.montant_ttc}€ le {a.date_ecriture} et {b.montant_ttc}€ le {b.date_ecriture}"
                    ),
                    ecriture_id_1=a.id,
                    ecriture_id_2=b.id,
                )
            )
    return anomalies


def detecter_date_hors_exercice(
    ecriture_id: str, date_ecriture: date, date_debut_exercice: date, date_fin_exercice: date
) -> Anomalie | None:
    if date_ecriture < date_debut_exercice or date_ecriture > date_fin_exercice:
        return Anomalie(
            type=TypeAnomalie.DATE_HORS_EXERCICE,
            message=(
                f"Date {date_ecriture} hors de l'exercice "
                f"({date_debut_exercice} — {date_fin_exercice})"
            ),
            ecriture_id_1=ecriture_id,
        )
    return None


TAUX_TVA_LEGAUX_FRANCE = {Decimal("0"), Decimal("2.1"), Decimal("5.5"), Decimal("10"), Decimal("20")}


def detecter_taux_tva_inconnu(ecriture_id: str, taux_tva: Decimal) -> Anomalie | None:
    if taux_tva not in TAUX_TVA_LEGAUX_FRANCE:
        return Anomalie(
            type=TypeAnomalie.TAUX_TVA_INCONNU,
            message=f"Taux de TVA {taux_tva}% non reconnu parmi les taux légaux français",
            ecriture_id_1=ecriture_id,
        )
    return None
