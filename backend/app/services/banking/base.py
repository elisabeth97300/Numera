"""
Interface commune que tout connecteur bancaire (Bridge, Powens, ou un futur
fournisseur DSP2) doit implémenter. Le reste de l'application (notamment
reconciliation_service.py) dépend de cette interface, jamais d'un fournisseur
concret directement — pour pouvoir changer de fournisseur, ou en supporter
plusieurs simultanément, sans toucher à la logique de rapprochement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class CompteBancaireExterne:
    id_externe: str
    nom: str
    iban_masque: str
    solde: Decimal


@dataclass
class TransactionExterne:
    id_externe: str
    date_operation: date
    libelle: str
    montant: Decimal  # positif = encaissement, négatif = décaissement, même convention que LigneReleve


class BankingConnector(ABC):
    """Contrat que Bridge/Powens/etc. doivent respecter."""

    @abstractmethod
    def lister_comptes(self, id_utilisateur_externe: str) -> list[CompteBancaireExterne]:
        ...

    @abstractmethod
    def recuperer_transactions(
        self, id_utilisateur_externe: str, compte_id_externe: str, depuis: date
    ) -> list[TransactionExterne]:
        ...

    @abstractmethod
    def generer_url_connexion(self, redirect_uri: str) -> str:
        """URL vers laquelle rediriger l'utilisateur pour connecter sa banque (parcours DSP2 standard)."""
        ...
