"""
Logique métier pure des états financiers : balance (cumuls par compte, en
partant du solde d'ouverture), classement bilan (actif/passif) et compte de
résultat (charges/produits) par classe PCG.

Réutilise le concept de BalanceCompte déjà défini dans exercice_domain.py
(même structure, même sémantique) pour éviter deux représentations
différentes de la même chose.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.exercice_domain import BalanceCompte, LigneSolde


@dataclass
class MouvementCompte:
    compte_pcg: str
    debit: Decimal
    credit: Decimal


def construire_balance(solde_ouverture: list[LigneSolde], mouvements: list[MouvementCompte]) -> list[BalanceCompte]:
    """
    Balance = solde d'ouverture + mouvements de l'exercice, cumulés par
    compte. C'est la même logique que le calcul déjà fait à la clôture d'un
    exercice (exercice_domain.calculer_solde_ouverture_suivant), mais dans
    l'autre sens : ici on veut voir l'état courant, pas encore clôturé.
    """
    cumuls: dict[str, dict[str, Decimal]] = {}

    for ligne in solde_ouverture:
        c = cumuls.setdefault(ligne.compte_pcg, {"debit": Decimal("0"), "credit": Decimal("0")})
        c["debit"] += ligne.solde_debit
        c["credit"] += ligne.solde_credit

    for m in mouvements:
        c = cumuls.setdefault(m.compte_pcg, {"debit": Decimal("0"), "credit": Decimal("0")})
        c["debit"] += m.debit
        c["credit"] += m.credit

    return [
        BalanceCompte(compte_pcg=compte, total_debit=v["debit"], total_credit=v["credit"])
        for compte, v in sorted(cumuls.items())
    ]


@dataclass
class PosteBilan:
    compte_pcg: str
    libelle: str
    montant: Decimal


@dataclass
class Bilan:
    actif: list[PosteBilan]
    passif: list[PosteBilan]

    def total_actif(self) -> Decimal:
        return sum((p.montant for p in self.actif), Decimal("0"))

    def total_passif(self) -> Decimal:
        return sum((p.montant for p in self.passif), Decimal("0"))

    def est_equilibre(self) -> bool:
        return self.total_actif() == self.total_passif()


# Classement simplifié par première position du compte PCG. Un vrai plan
# comptable distingue davantage (ex: 2xx immobilisations vs 3xx stocks vs
# 5xx trésorerie côté actif) — suffisant pour un MVP, à affiner avec un
# référentiel PCG complet plus tard.
CLASSES_ACTIF = {2, 3, 5}  # immobilisations, stocks, trésorerie
CLASSES_PASSIF = {1, 4}  # capitaux propres, dettes (dont fournisseurs)


def construire_bilan(balance: list[BalanceCompte]) -> Bilan:
    actif: list[PosteBilan] = []
    passif: list[PosteBilan] = []

    for compte in balance:
        classe = int(compte.compte_pcg[0])
        solde = compte.solde()
        if solde == 0:
            continue

        if classe in CLASSES_ACTIF:
            actif.append(PosteBilan(compte.compte_pcg, f"Compte {compte.compte_pcg}", abs(solde)))
        elif classe in CLASSES_PASSIF:
            passif.append(PosteBilan(compte.compte_pcg, f"Compte {compte.compte_pcg}", abs(solde)))
        # classe 6/7 (gestion) : n'apparaissent pas au bilan, seulement au
        # compte de résultat — cf. construire_compte_resultat ci-dessous.

    return Bilan(actif=actif, passif=passif)


@dataclass
class CompteResultat:
    charges: list[PosteBilan]
    produits: list[PosteBilan]

    def total_charges(self) -> Decimal:
        return sum((p.montant for p in self.charges), Decimal("0"))

    def total_produits(self) -> Decimal:
        return sum((p.montant for p in self.produits), Decimal("0"))

    def resultat_net(self) -> Decimal:
        return self.total_produits() - self.total_charges()


def construire_compte_resultat(balance: list[BalanceCompte]) -> CompteResultat:
    charges: list[PosteBilan] = []
    produits: list[PosteBilan] = []

    for compte in balance:
        classe = int(compte.compte_pcg[0])
        if classe == 6:
            montant = compte.total_debit - compte.total_credit
            if montant != 0:
                charges.append(PosteBilan(compte.compte_pcg, f"Compte {compte.compte_pcg}", montant))
        elif classe == 7:
            montant = compte.total_credit - compte.total_debit
            if montant != 0:
                produits.append(PosteBilan(compte.compte_pcg, f"Compte {compte.compte_pcg}", montant))

    return CompteResultat(charges=charges, produits=produits)


@dataclass
class RatiosFinanciers:
    resultat_net: Decimal
    total_charges: Decimal
    total_produits: Decimal
    taux_marge: Decimal | None  # résultat net / produits, en %


def calculer_ratios(compte_resultat: CompteResultat) -> RatiosFinanciers:
    produits = compte_resultat.total_produits()
    resultat = compte_resultat.resultat_net()
    taux_marge = (resultat / produits * 100) if produits > 0 else None
    return RatiosFinanciers(
        resultat_net=resultat,
        total_charges=compte_resultat.total_charges(),
        total_produits=produits,
        taux_marge=taux_marge,
    )
