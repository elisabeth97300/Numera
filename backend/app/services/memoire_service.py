from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.memoire_domain import (
    HistoriqueTiers,
    SuggestionMemoire,
    normaliser_tiers,
    suggerer_depuis_memoire,
)
from app.models.habitude import HabitudeComptable


def enregistrer_confirmation(db: Session, client_id: UUID, tiers: str, compte_pcg: str) -> None:
    """
    Appelée à chaque validation d'une proposition (cf. proposition_service.valider) :
    incrémente le compteur si l'association tiers/compte existe déjà pour ce
    client, la crée sinon. C'est le mécanisme d'apprentissage — aucune
    intervention manuelle requise.
    """
    tiers_normalise = normaliser_tiers(tiers)
    habitude = db.scalar(
        select(HabitudeComptable).where(
            HabitudeComptable.client_id == client_id,
            HabitudeComptable.tiers_normalise == tiers_normalise,
            HabitudeComptable.compte_pcg == compte_pcg,
        )
    )
    if habitude:
        habitude.nombre_confirmations += 1
    else:
        db.add(
            HabitudeComptable(
                client_id=client_id, tiers_normalise=tiers_normalise, compte_pcg=compte_pcg, nombre_confirmations=1
            )
        )
    db.commit()


def obtenir_suggestion(db: Session, client_id: UUID, tiers: str) -> SuggestionMemoire | None:
    tiers_normalise = normaliser_tiers(tiers)
    rows = db.scalars(
        select(HabitudeComptable).where(
            HabitudeComptable.client_id == client_id, HabitudeComptable.tiers_normalise == tiers_normalise
        )
    )
    historiques = [HistoriqueTiers(r.tiers_normalise, r.compte_pcg, r.nombre_confirmations) for r in rows]
    return suggerer_depuis_memoire(tiers, historiques)
