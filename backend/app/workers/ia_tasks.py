from uuid import UUID

from app.core.database import SessionLocal
from app.domain.memoire_domain import combiner_confiance
from app.domain.proposition_domain import valider_proposition
from app.models.document import DocumentSource
from app.models.proposition import PropositionIA, StatutProposition
from app.services import ia_comptable_service, memoire_service
from app.workers.celery_app import celery_app


@celery_app.task(name="ia_tasks.generer_proposition", bind=True, max_retries=3)
def generer_proposition(self, document_id: str):
    db = SessionLocal()
    try:
        document = db.get(DocumentSource, UUID(document_id))
        if document is None or not document.donnees_extraites:
            return {"erreur": "document introuvable ou non encore traité par l'OCR"}

        texte_ocr = document.donnees_extraites.get("texte_brut", "")
        confiance_ocr = 1.0 - 0.0  # score global déjà pris en compte côté OCR ; affiné ci-dessous si dispo
        champs = document.donnees_extraites.get("champs", [])
        if champs:
            confiance_ocr = sum(c["confiance"] for c in champs) / len(champs)

        try:
            brute = ia_comptable_service.generer_proposition_brute(texte_ocr)

            montant_ttc_attendu = None
            for champ in champs:
                if champ["nom"] == "montant_ttc":
                    from decimal import Decimal

                    montant_ttc_attendu = Decimal(champ["valeur"])

            validee = valider_proposition(brute, montant_ttc_attendu=montant_ttc_attendu)

            # Consulte le moteur de mémoire : ce tiers a-t-il déjà une
            # habitude connue pour ce client ? Combine avec la confiance
            # OCR/LLM pour décider du score final et si une vérification
            # prioritaire s'impose (cf. domain/memoire_domain.combiner_confiance).
            suggestion_memoire = memoire_service.obtenir_suggestion(db, document.client_id, validee.tiers)
            decision = combiner_confiance(
                confiance_ocr=confiance_ocr,
                confiance_llm=validee.score_confiance,
                suggestion_memoire=suggestion_memoire,
                compte_propose_llm=validee.compte_pcg,
            )

            avertissements = list(validee.avertissements)
            if decision.source_principale == "conflit_memoire_llm" and suggestion_memoire:
                avertissements.append(
                    f"L'IA propose {validee.compte_pcg} mais l'historique de ce client utilise habituellement "
                    f"{suggestion_memoire.compte_pcg} pour ce tiers"
                )

            proposition = PropositionIA(
                document_source_id=document.id,
                compte_propose=validee.compte_pcg,
                tiers_propose=validee.tiers,
                montant_ht=validee.montant_ht,
                montant_tva=validee.montant_tva,
                taux_tva=validee.taux_tva,
                score_confiance=decision.confiance_finale,
                a_verifier_en_priorite=validee.a_verifier_en_priorite or not decision.peut_auto_valider and decision.source_principale == "conflit_memoire_llm",
                avertissements=avertissements or None,
                statut=StatutProposition.EN_ATTENTE,
            )
            db.add(proposition)
            db.commit()

        except Exception as exc:  # noqa: BLE001
            raise self.retry(exc=exc, countdown=30) from exc

    finally:
        db.close()
