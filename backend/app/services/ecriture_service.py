from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.ecriture_domain import construire_ecriture_depuis_proposition, extourner
from app.models.ecriture import Ecriture, Journal, LigneEcriture, StatutEcriture
from app.services import exercice_service

# Comptes par défaut pour une facture d'achat standard — à affiner plus tard
# par un référentiel PCG complet mappé sur le compte proposé par l'IA
# (ex: taux de TVA -> compte 445660/445620 selon déductible/collectée).
COMPTE_TVA_DEDUCTIBLE = "445660"
COMPTE_FOURNISSEURS = "401000"


def creer_ecriture_depuis_proposition(
    db: Session,
    client_id: UUID,
    exercice_id: UUID,
    compte_charge: str,
    tiers: str,
    montant_ht: Decimal,
    montant_tva: Decimal,
    libelle: str,
    date_ecriture,
    valide_par: UUID,
) -> Ecriture:
    """
    Transforme une proposition validée en écriture réelle. Vérifie d'abord
    que l'exercice n'est pas clôturé (garde-fou légal, cf. étape 5bis) avant
    de construire les lignes en partie double.
    """
    exercice_service.verifier_avant_ecriture(db, exercice_id)  # lève ExerciceError si clôturé

    lignes_domaine = construire_ecriture_depuis_proposition(
        compte_charge_ou_produit=compte_charge,
        compte_tva=COMPTE_TVA_DEDUCTIBLE if montant_tva > 0 else None,
        compte_tiers=COMPTE_FOURNISSEURS,
        tiers=tiers,
        montant_ht=montant_ht,
        montant_tva=montant_tva,
        libelle_base=libelle,
    )  # équilibre déjà vérifié par le domaine

    ecriture = Ecriture(
        client_id=client_id,
        exercice_id=exercice_id,
        journal=Journal.ACHATS,
        date_ecriture=date_ecriture,
        libelle=libelle,
        valide_par=valide_par,
        statut=StatutEcriture.VALIDEE,
    )
    db.add(ecriture)
    db.flush()

    for ligne in lignes_domaine:
        db.add(
            LigneEcriture(
                ecriture_id=ecriture.id,
                compte_pcg=ligne.compte_pcg,
                libelle=ligne.libelle,
                debit=ligne.debit,
                credit=ligne.credit,
            )
        )

    db.commit()
    db.refresh(ecriture)
    return ecriture


def extourner_ecriture(db: Session, ecriture_id: UUID, valide_par: UUID) -> Ecriture:
    """Crée l'écriture inverse d'une écriture existante, sans jamais supprimer l'originale."""
    originale = db.get(Ecriture, ecriture_id)
    if originale is None:
        raise ValueError("Écriture introuvable")

    exercice_service.verifier_avant_ecriture(db, originale.exercice_id)

    from app.domain.ecriture_domain import LigneEcritureDomaine

    lignes_domaine = [
        LigneEcritureDomaine(l.compte_pcg, l.libelle or "", debit=Decimal(str(l.debit)), credit=Decimal(str(l.credit)))
        for l in originale.lignes
    ]
    lignes_extourne = extourner(lignes_domaine)

    extourne = Ecriture(
        client_id=originale.client_id,
        exercice_id=originale.exercice_id,
        journal=originale.journal,
        date_ecriture=originale.date_ecriture,
        libelle=f"Extourne — {originale.libelle}",
        valide_par=valide_par,
        statut=StatutEcriture.VALIDEE,
    )
    db.add(extourne)
    db.flush()

    for ligne in lignes_extourne:
        db.add(
            LigneEcriture(
                ecriture_id=extourne.id,
                compte_pcg=ligne.compte_pcg,
                libelle=ligne.libelle,
                debit=ligne.debit,
                credit=ligne.credit,
            )
        )

    db.commit()
    db.refresh(extourne)
    return extourne


def lister_ecritures(db: Session, client_id: UUID, journal: str | None = None) -> list[Ecriture]:
    stmt = select(Ecriture).where(Ecriture.client_id == client_id)
    if journal:
        stmt = stmt.where(Ecriture.journal == journal)
    return list(db.scalars(stmt))
