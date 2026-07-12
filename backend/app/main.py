"""
Point d'entrée FastAPI. Assemble les routeurs de chaque module et configure le
CORS pour autoriser le frontend (déployé sur Vercel) à appeler cette API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import anomalies, assistant, auth, clients, documents, ecritures, exercices, graphe, propositions, reconciliation, reporting, tva
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de ComptaCopilot AI — copilote IA pour cabinets comptables.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(clients.router, prefix=settings.api_v1_prefix)
app.include_router(documents.router, prefix=settings.api_v1_prefix)
app.include_router(propositions.router, prefix=settings.api_v1_prefix)
app.include_router(ecritures.router, prefix=settings.api_v1_prefix)
app.include_router(ecritures.router_global, prefix=settings.api_v1_prefix)
app.include_router(anomalies.router, prefix=settings.api_v1_prefix)
app.include_router(reconciliation.router, prefix=settings.api_v1_prefix)
app.include_router(assistant.router, prefix=settings.api_v1_prefix)
app.include_router(graphe.router, prefix=settings.api_v1_prefix)
app.include_router(reporting.router, prefix=settings.api_v1_prefix)
app.include_router(tva.router, prefix=settings.api_v1_prefix)
app.include_router(exercices.router, prefix=settings.api_v1_prefix)
app.include_router(exercices.router_global, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def health_check():
    """Utilisé par la plateforme d'hébergement (Railway/Render) pour vérifier que l'app répond."""
    return {"status": "ok", "app": settings.app_name}

# Création automatique des tables au démarrage
from app.core.database import Base, engine
from app.models.organisation import Organisation, Utilisateur
from app.models.client import Client
from app.models.document import Document
from app.models.ecriture import Ecriture
from app.models.exercice import Exercice
from app.models.habitude import Habitude
from app.models.proposition import Proposition
from app.models.releve_bancaire import ReleveBancaire

Base.metadata.create_all(bind=engine)
