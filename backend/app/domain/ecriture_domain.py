"""
Logique métier pure des écritures comptables : équilibre débit/crédit,
extourne (contre-passation). Cohérent avec exercice_domain.py : aucune
dépendance framework, tout est testable en pur Python.
"""

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import Enum


class EcritureError(Exception):
    """Erreur métier liée à une écriture comptable."""


@dataclass
class LigneEcritureDomaine:
    compte_pcg: str
    libelle: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")

    def __post_init__(self):
        if self.debit < 0 or self.credit < 0:
            raise EcritureError("Un montant débit/crédit ne peut pas être négatif")
        if self.debit > 0 and self.credit > 0:
            raise EcritureError(
                f"La ligne sur le compte {self.compte_pcg} ne peut pas être à la fois "
                f"débitrice et créditrice"
            )
        if self.debit == 0 and self.credit == 0:
            raise EcritureError(f"La ligne sur le compte {self.compte_pcg} doit avoir un montant non nul")


def valider_equilibre(lignes: list[LigneEcritureDomaine]) -> None:
    """Le cœur de la partie double : total débit == total crédit, sur CHAQUE écriture."""
    if len(lignes) < 2:
        raise EcritureError("Une écriture en partie double nécessite au moins deux lignes")

    total_debit = sum((l.debit for l in lignes), Decimal("0"))
    total_credit = sum((l.credit for l in lignes), Decimal("0"))
    if total_debit != total_credit:
        raise EcritureError(
            f"Écriture déséquilibrée : débit={total_debit} crédit={total_credit}"
        )


def extourner(lignes: list[LigneEcritureDomaine]) -> list[LigneEcritureDomaine]:
    """
    Génère les lignes de contre-passation (extourne) d'une écriture : chaque
    débit devient un crédit de même montant et inversement. Utilisée pour
    annuler une écriture déjà validée sans jamais la supprimer — la piste
    d'audit doit rester intacte (cf. principe directeur de l'architecture).
    """
    return [
        LigneEcritureDomaine(
            compte_pcg=l.compte_pcg,
            libelle=f"Extourne — {l.libelle}",
            debit=l.credit,
            credit=l.debit,
        )
        for l in lignes
    ]


def construire_ecriture_depuis_proposition(
    compte_charge_ou_produit: str,
    compte_tva: str | None,
    compte_tiers: str,
    tiers: str,
    montant_ht: Decimal,
    montant_tva: Decimal,
    libelle_base: str,
) -> list[LigneEcritureDomaine]:
    """
    Construit les lignes en partie double d'une facture d'achat standard à
    partir d'une proposition validée :
    - débit du compte de charge (HT)
    - débit du compte de TVA déductible (si TVA non nulle)
    - crédit du compte fournisseur (TTC)
    """
    montant_ttc = montant_ht + montant_tva
    lignes = [LigneEcritureDomaine(compte_charge_ou_produit, libelle_base, debit=montant_ht)]

    if montant_tva > 0:
        if compte_tva is None:
            raise EcritureError("Un montant de TVA non nul nécessite un compte de TVA")
        lignes.append(LigneEcritureDomaine(compte_tva, f"TVA déductible — {libelle_base}", debit=montant_tva))

    lignes.append(LigneEcritureDomaine(compte_tiers, f"{tiers} — {libelle_base}", credit=montant_ttc))

    valider_equilibre(lignes)  # ceinture + bretelles avant de retourner les lignes
    return lignes
