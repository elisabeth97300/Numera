"""
Service de pilotage : construit les données réelles (trésorerie, rentabilité
clients, comparaison de résultats, dépenses réductibles, alertes) à partir de
la base, en s'appuyant sur les fonctions pures des modules domaine
correspondants. C'est ce service que l'assistant conversationnel appelle
comme "outils" pour répondre aux questions du dirigeant.
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.alerte_domain import (
    alerte_anomalies,
    alerte_exercice_proche_cloture,
    alerte_risque_tresorerie,
    alerte_tva_a_payer,
    prioriser_alertes,
)
from app.domain.depenses_domain import identifier_depenses_reductibles
from app.domain.pilotage_domain import MouvementClient, PosteComparatif, calculer_rentabilite_clients, comparer_resultats
from app.domain.tresorerie_domain import MouvementJournalier, projeter_tresorerie
from app.models.ecriture import Ecriture, LigneEcriture
from app.models.exercice import ExerciceComptable
from app.services import anomaly_service, reporting_service, tva_service

COMPTE_BANQUE = "512000"


def obtenir_projection_tresorerie(db: Session, client_id: UUID, exercice_id: UUID, horizon_jours: int = 90):
    """
    Reconstruit un historique de mouvements journaliers nets sur le compte
    banque à partir des écritures existantes, puis projette. Le "solde
    actuel" est calculé comme le solde du compte banque à date, pas comme un
    solde bancaire réel importé (à améliorer une fois l'intégration bancaire
    en place — cf. limites documentées).
    """
    rows = db.execute(
        select(Ecriture.date_ecriture, LigneEcriture.debit, LigneEcriture.credit)
        .join(Ecriture, LigneEcriture.ecriture_id == Ecriture.id)
        .where(Ecriture.exercice_id == exercice_id, LigneEcriture.compte_pcg == COMPTE_BANQUE)
        .order_by(Ecriture.date_ecriture)
    ).all()

    cumuls_par_jour: dict[date, Decimal] = {}
    solde = Decimal("0")
    for d, debit, credit in rows:
        net = Decimal(str(debit or 0)) - Decimal(str(credit or 0))
        cumuls_par_jour[d] = cumuls_par_jour.get(d, Decimal("0")) + net
        solde += net

    mouvements = [MouvementJournalier(date=d, montant_net=m) for d, m in sorted(cumuls_par_jour.items())]
    return projeter_tresorerie(solde, mouvements, horizon_jours)


def obtenir_rentabilite_clients(db: Session, client_id: UUID, exercice_id: UUID):
    """
    Approxime le chiffre d'affaires par client à partir du libellé des
    écritures de vente (même limite que anomaly_service : le tiers n'est pas
    encore un champ dédié). charges_attribuables reste à 0 en l'absence de
    comptabilité analytique.
    """
    rows = db.execute(
        select(Ecriture.libelle, LigneEcriture.credit)
        .join(Ecriture, LigneEcriture.ecriture_id == Ecriture.id)
        .where(Ecriture.exercice_id == exercice_id, Ecriture.journal == "ventes")
    ).all()

    mouvements = []
    for libelle, credit in rows:
        if not credit:
            continue
        tiers = libelle.split("—")[-1].strip() if "—" in libelle else libelle
        mouvements.append(MouvementClient(tiers=tiers, chiffre_affaires=Decimal(str(credit))))

    return calculer_rentabilite_clients(mouvements)


def obtenir_comparaison_resultats(db: Session, exercice_id: UUID):
    """Compare le compte de résultat de l'exercice courant à celui de l'exercice précédent (s'il existe)."""
    exercice = db.get(ExerciceComptable, exercice_id)
    if exercice is None or exercice.exercice_precedent_id is None:
        return None

    cr_courant = reporting_service.obtenir_compte_resultat(db, exercice_id)
    cr_precedent = reporting_service.obtenir_compte_resultat(db, exercice.exercice_precedent_id)

    charges_precedent = {p.compte_pcg: p.montant for p in cr_precedent.charges}
    produits_precedent = {p.compte_pcg: p.montant for p in cr_precedent.produits}

    charges_comp = [
        PosteComparatif(p.compte_pcg, p.montant, charges_precedent.get(p.compte_pcg, Decimal("0")))
        for p in cr_courant.charges
    ]
    produits_comp = [
        PosteComparatif(p.compte_pcg, p.montant, produits_precedent.get(p.compte_pcg, Decimal("0")))
        for p in cr_courant.produits
    ]

    return comparer_resultats(charges_comp, produits_comp, cr_courant.resultat_net(), cr_precedent.resultat_net())


def obtenir_depenses_reductibles(db: Session, exercice_id: UUID):
    cr = reporting_service.obtenir_compte_resultat(db, exercice_id)
    comptes = {p.compte_pcg: p.montant for p in cr.charges}
    return identifier_depenses_reductibles(comptes)


def obtenir_alertes(db: Session, client_id: UUID, exercice_id: UUID) -> list:
    exercice = db.get(ExerciceComptable, exercice_id)
    aujourdhui = date.today()

    candidats = []

    try:
        projection = obtenir_projection_tresorerie(db, client_id, exercice_id)
        candidats.append(alerte_risque_tresorerie(projection.scenario_pessimiste, projection.horizon_jours))
    except Exception:  # noqa: BLE001  — historique insuffisant, pas bloquant pour les autres alertes
        pass

    anomalies = anomaly_service.detecter_anomalies_client(db, client_id)
    candidats.append(alerte_anomalies(len(anomalies)))

    try:
        prep_tva = tva_service.obtenir_preparation_tva(db, exercice_id)
        # échéance simplifiée : le 20 du mois suivant, hypothèse régime réel normal mensuel
        date_echeance = (aujourdhui.replace(day=1) + timedelta(days=32)).replace(day=20)
        candidats.append(alerte_tva_a_payer(prep_tva.solde_a_payer(), date_echeance, aujourdhui))
    except Exception:  # noqa: BLE001
        pass

    if exercice:
        candidats.append(alerte_exercice_proche_cloture(exercice.date_fin, aujourdhui, exercice.statut.value))

    return prioriser_alertes(candidats)
