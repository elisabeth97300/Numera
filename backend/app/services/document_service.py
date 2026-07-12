from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.document_domain import DocumentError, TypeDocument as TypeDocumentDomain, calculer_hash, valider_fichier
from app.models.document import DocumentSource, StatutOCR
from app.services import storage_service


def importer_document(
    db: Session, client_id: UUID, nom_fichier: str, contenu: bytes, type_document: str
) -> tuple[DocumentSource, DocumentSource | None]:
    """
    Importe un document : valide le fichier, vérifie s'il s'agit d'un doublon
    exact (même hash déjà présent pour ce client) puis, si non, le stocke et
    met le traitement OCR en file d'attente.

    Retourne (document_créé, document_doublon_existant_ou_None). Le document
    est créé même en cas de doublon détecté — c'est à l'appelant (l'API) de
    décider s'il bloque l'import ou laisse le comptable trancher ; on ne
    perd jamais l'information qu'un doublon a été repéré.
    """
    type_enum = TypeDocumentDomain(type_document)
    valider_fichier(nom_fichier, len(contenu), type_enum)  # lève DocumentError si invalide

    hash_fichier = calculer_hash(contenu)
    doublon = db.scalar(
        select(DocumentSource).where(
            DocumentSource.client_id == client_id, DocumentSource.hash_fichier == hash_fichier
        )
    )

    cle_s3 = storage_service.uploader_fichier(str(client_id), nom_fichier, contenu)

    document = DocumentSource(
        client_id=client_id,
        type_document=type_document,
        fichier_s3_url=cle_s3,
        statut_ocr=StatutOCR.EN_ATTENTE,
        hash_fichier=hash_fichier,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if doublon is None:
        # Import différé pour éviter une dépendance dure à Celery/Redis dans
        # les tests qui n'ont pas besoin de la file d'attente.
        from app.workers.ocr_tasks import traiter_document

        traiter_document.delay(str(document.id))

    return document, doublon


def obtenir_document(db: Session, document_id: UUID) -> DocumentSource | None:
    return db.get(DocumentSource, document_id)
