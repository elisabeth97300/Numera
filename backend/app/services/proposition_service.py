from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import DocumentSource
from app.models.proposition import PropositionIA, StatutProposition
from app.services import ecriture_service, memoire_service


def lister_propositions(db: Session, client_id: UUID, statut: str | None = None) -> list[PropositionIA]:
    stmt = (
        select(PropositionIA)
        .join(DocumentSource, PropositionIA.document_source_id == DocumentSource.id)
        .where(DocumentSource.client_id == client_id)
    )
    if statut:
        stmt = stmt.where(PropositionIA.statut == statut)
    return list(db.scalars(stmt))


def valider(db: Session, proposition_id: UUID, exercice_id: UUID, valide_par: UUID) -> PropositionIA:
    """
    Transforme la proposition en écriture réelle (via ecriture_service, qui
    vérifie que l'exercice n'est pas clôturé) puis marque la proposition
    comme validée et la lie à l'écriture créée.
    """
    proposition = db.get(PropositionIA, proposition_id)
    if proposition is None:
        raise ValueError("Proposition introuvable")
    if proposition.statut != StatutProposition.EN_ATTENTE:
        raise ValueError(f"Proposition déjà traitée (statut : {proposition.statut.value})")

    document = db.get(DocumentSource, proposition.document_source_id)

    ecriture = ecriture_service.creer_ecriture_depuis_proposition(
        db,
        client_id=document.client_id,
        exercice_id=exercice_id,
        compte_charge=proposition.compte_propose,
        tiers=proposition.tiers_propose,
        montant_ht=Decimal(str(proposition.montant_ht)),
        montant_tva=Decimal(str(proposition.montant_tva)),
        libelle=f"{proposition.tiers_propose} — proposition IA",
        date_ecriture=date.today(),
        valide_par=valide_par,
    )

    proposition.statut = StatutProposition.VALIDEE
    proposition.ecriture_id = ecriture.id
    db.commit()
    db.refresh(proposition)

    # Apprentissage : mémorise l'association tiers -> compte pour ce client,
    # afin que la prochaine facture du même fournisseur bénéficie d'une
    # confiance plus élevée sans redemander au LLM de deviner à nouveau.
    memoire_service.enregistrer_confirmation(db, document.client_id, proposition.tiers_propose, proposition.compte_propose)

    return proposition


def modifier(db: Session, proposition_id: UUID, corrections: dict) -> PropositionIA:
    """
    Le comptable corrige un ou plusieurs champs avant validation (ex: mauvais
    compte proposé). La proposition passe en statut 'modifiee' — elle reste
    en attente d'un appel explicite à `valider` ensuite.
    """
    proposition = db.get(PropositionIA, proposition_id)
    if proposition is None:
        raise ValueError("Proposition introuvable")
    if proposition.statut != StatutProposition.EN_ATTENTE:
        raise ValueError(f"Proposition déjà traitée (statut : {proposition.statut.value})")

    for champ, valeur in corrections.items():
        if valeur is not None:
            setattr(proposition, champ, valeur)
    proposition.statut = StatutProposition.MODIFIEE
    db.commit()
    db.refresh(proposition)
    return proposition


def rejeter(db: Session, proposition_id: UUID) -> PropositionIA:
    proposition = db.get(PropositionIA, proposition_id)
    if proposition is None:
        raise ValueError("Proposition introuvable")
    proposition.statut = StatutProposition.REJETEE
    db.commit()
    db.refresh(proposition)
    return proposition
