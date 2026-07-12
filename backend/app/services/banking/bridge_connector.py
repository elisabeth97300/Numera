"""
Connecteur Bridge (https://bridgeapi.io) — agrégateur bancaire français
conforme DSP2, utilisé par de nombreuses fintechs pour la connexion bancaire
automatique.

NOTE : implémentation structurelle non testée en conditions réelles (pas de
réseau ni de compte Bridge dans l'environnement de génération de ce code).
Nécessite BRIDGE_CLIENT_ID et BRIDGE_CLIENT_SECRET (cf. app/core/config.py)
et un compte partenaire Bridge actif avant mise en production.
"""

from datetime import date
from decimal import Decimal

import httpx

from app.core.config import get_settings
from app.services.banking.base import BankingConnector, CompteBancaireExterne, TransactionExterne

BASE_URL = "https://api.bridgeapi.io/v3"


class BridgeConnector(BankingConnector):
    def __init__(self):
        settings = get_settings()
        self._client_id = settings.bridge_client_id
        self._client_secret = settings.bridge_client_secret

    def _headers(self) -> dict:
        return {
            "Client-Id": self._client_id,
            "Client-Secret": self._client_secret,
            "Bridge-Version": "2025-01-15",
        }

    def generer_url_connexion(self, redirect_uri: str) -> str:
        response = httpx.post(
            f"{BASE_URL}/aggregation/connect-sessions",
            headers=self._headers(),
            json={"redirect_url": redirect_uri},
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()["url"]

    def lister_comptes(self, id_utilisateur_externe: str) -> list[CompteBancaireExterne]:
        response = httpx.get(
            f"{BASE_URL}/aggregation/accounts",
            headers={**self._headers(), "Bridge-User-Uuid": id_utilisateur_externe},
            timeout=15.0,
        )
        response.raise_for_status()
        return [
            CompteBancaireExterne(
                id_externe=str(c["id"]),
                nom=c["name"],
                iban_masque=c.get("iban", "")[-4:].rjust(len(c.get("iban", "")), "•"),
                solde=Decimal(str(c["balance"])),
            )
            for c in response.json()["resources"]
        ]

    def recuperer_transactions(
        self, id_utilisateur_externe: str, compte_id_externe: str, depuis: date
    ) -> list[TransactionExterne]:
        response = httpx.get(
            f"{BASE_URL}/aggregation/transactions",
            headers={**self._headers(), "Bridge-User-Uuid": id_utilisateur_externe},
            params={"account_id": compte_id_externe, "since": depuis.isoformat()},
            timeout=15.0,
        )
        response.raise_for_status()
        return [
            TransactionExterne(
                id_externe=str(t["id"]),
                date_operation=date.fromisoformat(t["date"]),
                libelle=t["clean_description"] or t["raw_description"],
                montant=Decimal(str(t["amount"])),
            )
            for t in response.json()["resources"]
        ]
