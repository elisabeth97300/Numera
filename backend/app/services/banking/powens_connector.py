"""
Connecteur Powens (ex-Budget Insight, https://powens.com) — alternative à
Bridge, également conforme DSP2. Même interface (BankingConnector) que
BridgeConnector : le reste de l'application n'a pas à savoir lequel est
utilisé pour un cabinet donné.

NOTE : mêmes réserves que bridge_connector.py — structurellement correct
selon la documentation Powens, non testé en conditions réelles ici.
"""

from datetime import date
from decimal import Decimal

import httpx

from app.core.config import get_settings
from app.services.banking.base import BankingConnector, CompteBancaireExterne, TransactionExterne

BASE_URL = "https://your-domain.biapi.pro/2.0"  # à remplacer par le domaine attribué par Powens


class PowensConnector(BankingConnector):
    def __init__(self):
        settings = get_settings()
        self._client_id = settings.powens_client_id
        self._client_secret = settings.powens_client_secret

    def generer_url_connexion(self, redirect_uri: str) -> str:
        response = httpx.get(
            f"{BASE_URL}/auth/webview/fr",
            params={"client_id": self._client_id, "redirect_uri": redirect_uri},
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()["url"]

    def lister_comptes(self, id_utilisateur_externe: str) -> list[CompteBancaireExterne]:
        response = httpx.get(
            f"{BASE_URL}/users/{id_utilisateur_externe}/accounts",
            headers={"Authorization": f"Bearer {self._client_secret}"},
            timeout=15.0,
        )
        response.raise_for_status()
        return [
            CompteBancaireExterne(
                id_externe=str(c["id"]),
                nom=c["name"],
                iban_masque=c.get("iban", ""),
                solde=Decimal(str(c["balance"])),
            )
            for c in response.json()["accounts"]
        ]

    def recuperer_transactions(
        self, id_utilisateur_externe: str, compte_id_externe: str, depuis: date
    ) -> list[TransactionExterne]:
        response = httpx.get(
            f"{BASE_URL}/users/{id_utilisateur_externe}/accounts/{compte_id_externe}/transactions",
            headers={"Authorization": f"Bearer {self._client_secret}"},
            params={"min_date": depuis.isoformat()},
            timeout=15.0,
        )
        response.raise_for_status()
        return [
            TransactionExterne(
                id_externe=str(t["id"]),
                date_operation=date.fromisoformat(t["date"]),
                libelle=t["wording"],
                montant=Decimal(str(t["value"])),
            )
            for t in response.json()["transactions"]
        ]
