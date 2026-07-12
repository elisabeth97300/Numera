"""
Logique métier pure de préparation de la déclaration de TVA : ventilation par
taux et calcul du solde à payer (TVA collectée - TVA déductible). Ne produit
pas le formulaire CA3 lui-même (mise en page administrative), seulement les
montants qui l'alimentent.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class LigneTVA:
    compte_pcg: str
    taux: Decimal
    montant_base_ht: Decimal
    montant_tva: Decimal
    sens: str  # "collectee" ou "deductible"


@dataclass
class VentilationTaux:
    taux: Decimal
    base_ht: Decimal
    montant_tva: Decimal


@dataclass
class PreparationTVA:
    collectee_par_taux: list[VentilationTaux]
    deductible_par_taux: list[VentilationTaux]

    def total_collectee(self) -> Decimal:
        return sum((v.montant_tva for v in self.collectee_par_taux), Decimal("0"))

    def total_deductible(self) -> Decimal:
        return sum((v.montant_tva for v in self.deductible_par_taux), Decimal("0"))

    def solde_a_payer(self) -> Decimal:
        """Positif = TVA à payer à l'État ; négatif = crédit de TVA."""
        return self.total_collectee() - self.total_deductible()


def preparer_tva(lignes: list[LigneTVA]) -> PreparationTVA:
    def ventiler(sens: str) -> list[VentilationTaux]:
        cumuls: dict[Decimal, dict[str, Decimal]] = {}
        for ligne in lignes:
            if ligne.sens != sens:
                continue
            c = cumuls.setdefault(ligne.taux, {"base": Decimal("0"), "tva": Decimal("0")})
            c["base"] += ligne.montant_base_ht
            c["tva"] += ligne.montant_tva
        return [
            VentilationTaux(taux=taux, base_ht=v["base"], montant_tva=v["tva"])
            for taux, v in sorted(cumuls.items())
        ]

    return PreparationTVA(
        collectee_par_taux=ventiler("collectee"),
        deductible_par_taux=ventiler("deductible"),
    )
