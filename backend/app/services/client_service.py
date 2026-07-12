from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.auth_domain import verifier_appartenance_organisation
from app.models.client import ClientDossier


def creer_client(db: Session, organisation_id: UUID, payload: dict) -> ClientDossier:
    client = ClientDossier(organisation_id=organisation_id, **payload)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def lister_clients(db: Session, organisation_id: UUID) -> list[ClientDossier]:
    return list(db.scalars(select(ClientDossier).where(ClientDossier.organisation_id == organisation_id)))


def obtenir_client(db: Session, client_id: UUID, organisation_id: UUID) -> ClientDossier | None:
    """
    Charge un client puis vérifie systématiquement qu'il appartient à
    l'organisation de l'utilisateur courant — jamais l'inverse (ne jamais
    filtrer la requête SQL par organisation_id seul sans ce garde-fou
    explicite, pour que l'isolation reste vraie même si un futur appel
    oublie le filtre).
    """
    client = db.get(ClientDossier, client_id)
    if client is None:
        return None
    verifier_appartenance_organisation(str(client.organisation_id), str(organisation_id))
    return client
