"""
Service applicatif de rapprochement bancaire.

Charge/persiste via SQLAlchemy et délègue toute décision (quelle ligne
correspond à quelle écriture, quand c'est ambigu, comment parser le CSV) à
app/domain/reconciliation_domain.py.
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.services.banking.base import BankingConnector

from app.domain.reconciliation_domain import (
    LigneEcritureBanque,
    LigneReleve,
    RapprochementError,
    StatutRapprochement,
    calculer_solde_rapprochement,
    generer_code_lettrage,
    parser_csv_releve,
    proposer_rapprochements,
    valider_lettrage_manuel,
)
from app.models.ecriture import Ecriture, LigneEcriture
from app.models.releve_bancaire import LigneReleveBancaire, StatutLigneReleve

# Compte banque par défaut du plan comptable — à rendre configurable par
# client si un cabinet gère plusieurs comptes bancaires pour un même dossier.
COMPTE_BANQUE_DEFAUT = "512000"


def importer_depuis_connecteur(
    db: Session, client_id: UUID, connecteur: "BankingConnector", id_utilisateur_externe: str, compte_id_externe: str, depuis
) -> dict:
    """
    Alternative à l'import CSV manuel : récupère directement les transactions
    via un connecteur open banking (Bridge, Powens...) et applique la même
    logique de rapprochement. `connecteur` est injecté plutôt qu'instancié
    ici, pour ne pas coupler ce service à un fournisseur précis — cf.
    app/services/banking/base.py.
    """
    transactions = connecteur.recuperer_transactions(id_utilisateur_externe, compte_id_externe, depuis)
    lignes_brutes = [(t.date_operation, t.libelle, t.montant) for t in transactions]
    return _traiter_lignes_releve(db, client_id, lignes_brutes)


def _traiter_lignes_releve(db: Session, client_id: UUID, lignes_brutes: list[tuple]) -> dict:
    """Logique commune à l'import CSV et à l'import via connecteur : persistance + proposition de rapprochement."""
    if not lignes_brutes:
        raise RapprochementError("Aucune ligne exploitable")

    lignes_releve_db = []
    for date_op, libelle, montant in lignes_brutes:
        ligne = LigneReleveBancaire(client_id=client_id, date_operation=date_op, libelle=libelle, montant=montant)
        db.add(ligne)
        lignes_releve_db.append(ligne)
    db.flush()

    lignes_releve_domaine = [
        LigneReleve(id=str(l.id), date=l.date_operation, libelle=l.libelle, montant=l.montant)
        for l in lignes_releve_db
    ]

    ecritures_banque = db.execute(
        select(LigneEcriture.id, Ecriture.date_ecriture, LigneEcriture.libelle, LigneEcriture.debit, LigneEcriture.credit)
        .join(Ecriture, LigneEcriture.ecriture_id == Ecriture.id)
        .where(Ecriture.client_id == client_id, LigneEcriture.compte_pcg == COMPTE_BANQUE_DEFAUT)
    ).all()
    lignes_ecriture_domaine = [
        LigneEcritureBanque(id=str(eid), date=d, libelle=lib or "", debit=Decimal(str(deb)), credit=Decimal(str(cre)))
        for eid, d, lib, deb, cre in ecritures_banque
    ]

    rapprochements = proposer_rapprochements(lignes_releve_domaine, lignes_ecriture_domaine)

    index_lettrage = _prochain_index_lettrage(db, client_id)
    for ligne_db, rapprochement in zip(lignes_releve_db, rapprochements):
        ligne_db.statut = StatutLigneReleve(rapprochement.statut.value)
        if rapprochement.ligne_ecriture_id:
            ligne_db.ligne_ecriture_id = UUID(rapprochement.ligne_ecriture_id)
            ligne_db.code_lettrage = generer_code_lettrage(index_lettrage)
            index_lettrage += 1

    db.commit()
    solde = calculer_solde_rapprochement(rapprochements)
    for ligne_db in lignes_releve_db:
        db.refresh(ligne_db)

    return {
        "lignes": lignes_releve_db,
        "rapprochements_par_id": {r.ligne_releve_id: r for r in rapprochements},
        "solde": solde,
    }


def importer_releve(db: Session, client_id: UUID, contenu_csv: bytes) -> dict:
    """
    Importe un relevé bancaire CSV, propose un rapprochement automatique
    contre les écritures existantes du compte banque, persiste le résultat.
    """
    lignes_brutes = parser_csv_releve(contenu_csv)
    if not lignes_brutes:
        raise RapprochementError("Aucune ligne exploitable dans le fichier")
    return _traiter_lignes_releve(db, client_id, lignes_brutes)


def _prochain_index_lettrage(db: Session, client_id: UUID) -> int:
    """Compte les lettrages déjà attribués pour ce client afin de ne jamais réutiliser un code."""
    return db.query(LigneReleveBancaire).filter(
        LigneReleveBancaire.client_id == client_id, LigneReleveBancaire.code_lettrage.isnot(None)
    ).count()


def lister_lignes_releve(db: Session, client_id: UUID) -> list[LigneReleveBancaire]:
    return list(db.scalars(select(LigneReleveBancaire).where(LigneReleveBancaire.client_id == client_id)))


def valider_lettrage(db: Session, ligne_releve_id: UUID, ligne_ecriture_id: UUID) -> LigneReleveBancaire:
    """Validation manuelle d'un rapprochement ambigu ou resté non rapproché."""
    ligne = db.get(LigneReleveBancaire, ligne_releve_id)
    if ligne is None:
        raise ValueError("Ligne de relevé introuvable")
    if ligne.statut == StatutLigneReleve.RAPPROCHE_AUTOMATIQUE:
        raise RapprochementError("Cette ligne est déjà rapprochée automatiquement")

    index_lettrage = _prochain_index_lettrage(db, ligne.client_id)
    ligne.ligne_ecriture_id = ligne_ecriture_id
    ligne.statut = StatutLigneReleve.RAPPROCHE_MANUEL
    ligne.code_lettrage = generer_code_lettrage(index_lettrage)
    db.commit()
    db.refresh(ligne)
    return ligne
