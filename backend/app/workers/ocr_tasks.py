"""
Tâche Celery : traite un document en file d'attente (OCR, puis transmission
à l'IA comptable pour proposer une écriture). Découplée de la requête HTTP
d'upload — le frontend consulte le statut via GET /documents/{id}/status ou
via WebSocket une fois cette route branchée.
"""

from uuid import UUID

from app.core.database import SessionLocal
from app.domain.document_domain import StatutOCR, necessite_relecture_manuelle
from app.models.document import DocumentSource
from app.services import ocr_service, storage_service
from app.workers.celery_app import celery_app


@celery_app.task(name="ocr_tasks.traiter_document", bind=True, max_retries=3)
def traiter_document(self, document_id: str):
    db = SessionLocal()
    try:
        document = db.get(DocumentSource, UUID(document_id))
        if document is None:
            return {"erreur": "document introuvable"}

        document.statut_ocr = StatutOCR.EN_COURS
        db.commit()

        try:
            contenu = storage_service._client.get_object(
                Bucket=storage_service.settings.s3_bucket_name, Key=document.fichier_s3_url
            )["Body"].read()
            extension = document.fichier_s3_url.rsplit(".", 1)[-1]

            resultat = ocr_service.lire_document(contenu, extension)

            document.donnees_extraites = {
                "texte_brut": resultat.texte_brut,
                "champs": [
                    {"nom": c.nom, "valeur": c.valeur, "confiance": c.confiance} for c in resultat.champs
                ],
                "necessite_relecture": necessite_relecture_manuelle(resultat),
            }
            document.statut_ocr = StatutOCR.TERMINE
            db.commit()

            # Étape suivante : déclencher la génération de la proposition IA
            # (voir app/workers/ia_tasks.py) — appel direct ici pour rester
            # simple dans ce squelette ; à faire évoluer vers une chaîne
            # Celery (`chain(...)`) si le volume le justifie.
            from app.workers.ia_tasks import generer_proposition

            generer_proposition.delay(str(document.id))

        except Exception as exc:  # noqa: BLE001
            document.statut_ocr = StatutOCR.ERREUR
            db.commit()
            raise self.retry(exc=exc, countdown=30) from exc

    finally:
        db.close()
