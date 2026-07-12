"""
Logique métier pure pour deux questions typiques d'un dirigeant :
- "Quels clients sont les moins rentables ?" -> classement par client
- "Pourquoi mon bénéfice baisse ?" -> comparaison période courante / précédente,
  postes qui expliquent le plus la variation.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class MouvementClient:
    tiers: str
    chiffre_affaires: Decimal = Decimal("0")
    charges_attribuables: Decimal = Decimal("0")  # souvent 0 en pratique, faute de comptabilité analytique


@dataclass
class RentabiliteClient:
    tiers: str
    chiffre_affaires: Decimal
    charges_attribuables: Decimal
    marge_estimee: Decimal


def calculer_rentabilite_clients(mouvements: list[MouvementClient]) -> list[RentabiliteClient]:
    """
    Cumule par tiers puis trie du moins rentable au plus rentable. Sans
    comptabilité analytique détaillée, `charges_attribuables` sera souvent 0 —
    dans ce cas le classement revient à trier par chiffre d'affaires
    croissant, ce qui reste une information utile ("quels clients pèsent le
    moins"), à ne pas confondre avec une vraie marge par client.
    """
    cumuls: dict[str, dict[str, Decimal]] = {}
    for m in mouvements:
        c = cumuls.setdefault(m.tiers, {"ca": Decimal("0"), "charges": Decimal("0")})
        c["ca"] += m.chiffre_affaires
        c["charges"] += m.charges_attribuables

    resultats = [
        RentabiliteClient(
            tiers=tiers, chiffre_affaires=v["ca"], charges_attribuables=v["charges"], marge_estimee=v["ca"] - v["charges"]
        )
        for tiers, v in cumuls.items()
    ]
    return sorted(resultats, key=lambda r: r.marge_estimee)


@dataclass
class PosteComparatif:
    compte_pcg: str
    montant_courant: Decimal
    montant_precedent: Decimal

    def variation(self) -> Decimal:
        return self.montant_courant - self.montant_precedent


@dataclass
class ComparaisonResultat:
    resultat_courant: Decimal
    resultat_precedent: Decimal
    charges_en_hausse: list[PosteComparatif]  # triées par hausse décroissante
    produits_en_baisse: list[PosteComparatif]  # triées par baisse décroissante

    def variation_resultat(self) -> Decimal:
        return self.resultat_courant - self.resultat_precedent


def comparer_resultats(
    charges_courantes: list[PosteComparatif],
    produits_courants: list[PosteComparatif],
    resultat_courant: Decimal,
    resultat_precedent: Decimal,
) -> ComparaisonResultat:
    """
    Identifie les postes qui expliquent le plus une variation de résultat :
    les charges dont le montant a le plus augmenté, et les produits dont le
    montant a le plus baissé. C'est la donnée factuelle qui alimente ensuite
    la réponse en langage naturel à "pourquoi mon bénéfice baisse ?".
    """
    charges_en_hausse = sorted(
        (c for c in charges_courantes if c.variation() > 0), key=lambda c: c.variation(), reverse=True
    )
    produits_en_baisse = sorted(
        (p for p in produits_courants if p.variation() < 0), key=lambda p: p.variation()
    )

    return ComparaisonResultat(
        resultat_courant=resultat_courant,
        resultat_precedent=resultat_precedent,
        charges_en_hausse=charges_en_hausse,
        produits_en_baisse=produits_en_baisse,
    )
