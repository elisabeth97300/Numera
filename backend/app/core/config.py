"""
Configuration centrale de l'application, lue depuis les variables d'environnement.
Utilise pydantic-settings pour valider les valeurs au démarrage plutôt que de
laisser une variable manquante planter l'app au milieu d'une requête.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    app_name: str = "ComptaCopilot AI"
    environment: str = "development"  # development | staging | production
    api_v1_prefix: str = "/api/v1"

    # Base de données
    database_url: str = "postgresql+psycopg://comptacopilot:comptacopilot@localhost:5432/comptacopilot"

    # Auth JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    # Stockage documents (S3 ou compatible MinIO en local)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket_name: str = "comptacopilot-documents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    # File d'attente
    redis_url: str = "redis://localhost:6379/0"

    # IA
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"

    # OCR — moteurs alternatifs (au-delà de Tesseract, déjà géré sans clé)
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    mistral_api_key: str = ""

    # Open banking — connecteurs (cf. app/services/banking/)
    bridge_client_id: str = ""
    bridge_client_secret: str = ""
    powens_client_id: str = ""
    powens_client_secret: str = ""

    # CORS — à restreindre à l'URL Vercel du frontend en production
    cors_allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
