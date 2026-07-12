"""
Service applicatif pour les exercices comptables.

Rôle : charger/persister via SQLAlchemy, et déléguer toute décision métier à
app/domain/exercice_domain.py. Ce fichier ne contient pas de règle comptable —
si un calcul ou une validation semble "logique métier", elle doit vivre dans le
domaine, pas ici.
"""

from decimal import Decimal
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import exercice_domain as domain
from app.models.exercice import ExerciceComptable, SoldeOuverture
# Ecriture / LigneEcriture : modèles définis à l'étape 5 (partie double), déjà
# décrits dans le schéma de données du document d'architecture. On suppose ici
# la structure : Ecriture(id, exercice_id, ...) <-1---n-> LigneEcriture(compte_pcg, debit, credit, ecriture_id).
from app.models.ecriture import Ecriture, LigneEcriture


def _to_domain_exercice(row: ExerciceComptable) -> domain.Exercice:
    return domain.Exercice(
        id=str(row.id),
        client_id=str(row.client_id),
        date_debut=row.date_debut,
        date_fin=row.date_fin,
        origine=domain.OrigineExercice(row.origine.value),
        statut=domain.StatutExercice(row.statut.value),
        exercice_precedent_id=str(row.exercice_precedent_id) if row.exercice_precedent_id else None,
    )


def demarrer_exercice(db: Session, exercice_id: UUID, lignes: list[dict] | None) -> ExerciceComptable:
    """
    Démarre un exercice. `lignes` = [{"compte_pcg": ..., "solde_debit": ..., "solde_credit": ...}, ...]
    Obligatoire et vérifié équilibré si l'exercice est `repris` (cf. domaine).
    """
    row = db.get(ExerciceComptable, exercice_id)
    if row is None:
        raise ValueError("Exercice introuvable")

    exercice_domaine = _to_domain_exercice(row)
    solde_domaine = None
    if lignes:
        solde_domaine = [
            domain.LigneSolde(
                compte_pcg=l["compte_pcg"],
                solde_debit=Decimal(str(l.get("solde_debit", 0))),
                solde_credit=Decimal(str(l.get("solde_credit", 0))),
                source=domain.SourceSolde.SAISIE_MANUELLE,
            )
            for l in lignes
        ]

    # Toute la logique (obligation du solde si "repris", vérification d'équilibre)
    # est appliquée ici et lève exercice_domain.ExerciceError si invalide.
    domain.demarrer_exercice(exercice_domaine, solde_domaine)

    # Persistance du résultat validé par le domaine
    row.statut = row.statut.__class__.EN_COURS
    if solde_domaine:
        for ligne in solde_domaine:
            db.add(
                SoldeOuverture(
                    exercice_id=row.id,
                    compte_pcg=ligne.compte_pcg,
                    solde_debit=ligne.solde_debit,
                    solde_credit=ligne.solde_credit,
                    source=SoldeOuverture.__table__.c.source.type.enum_class.SAISIE_MANUELLE,
                )
            )
    db.commit()
    db.refresh(row)
    return row


def verifier_avant_ecriture(db: Session, exercice_id: UUID) -> None:
    """
    À appeler systématiquement avant toute création/modification/suppression
    d'une ligne d'écriture. Lève domain.ExerciceError si l'exercice est
    clôturé ou archivé — c'est le point d'application concret de
    l'intangibilité légale des exercices clos.
    """
    row = db.get(ExerciceComptable, exercice_id)
    if row is None:
        raise ValueError("Exercice introuvable")
    domain.verifier_ecriture_modifiable(_to_domain_exercice(row))


def calculer_balance_finale(db: Session, exercice_id: UUID) -> list[domain.BalanceCompte]:
    """
    Construit la balance finale d'un exercice à partir des lignes d'écritures
    réellement enregistrées (somme des débits/crédits par compte). Utilisée
    juste avant la clôture.
    """
    rows = db.execute(
        select(
            LigneEcriture.compte_pcg,
            LigneEcriture.debit,
            LigneEcriture.credit,
        )
        .join(Ecriture, LigneEcriture.ecriture_id == Ecriture.id)
        .where(Ecriture.exercice_id == exercice_id)
    ).all()

    cumuls: dict[str, dict[str, Decimal]] = {}
    for compte_pcg, debit, credit in rows:
        cumul = cumuls.setdefault(compte_pcg, {"debit": Decimal("0"), "credit": Decimal("0")})
        cumul["debit"] += Decimal(str(debit or 0))
        cumul["credit"] += Decimal(str(credit or 0))

    return [
        domain.BalanceCompte(compte_pcg=compte, total_debit=v["debit"], total_credit=v["credit"])
        for compte, v in cumuls.items()
    ]


def cloturer_exercice(db: Session, exercice_id: UUID, cree_exercice_suivant: bool = True) -> dict:
    """
    Clôture un exercice et, si demandé, crée immédiatement l'exercice suivant
    avec son solde d'ouverture pré-rempli (origine = repris, source = cloture_auto).
    """
    row = db.get(ExerciceComptable, exercice_id)
    if row is None:
        raise ValueError("Exercice introuvable")

    exercice_domaine = _to_domain_exercice(row)
    balance_finale = calculer_balance_finale(db, exercice_id)

    # Toute la décision (équilibre requis, statut requis, calcul du report) est
    # dans le domaine — ici on ne fait que persister le résultat.
    _, solde_suivant = domain.cloturer_exercice(exercice_domaine, balance_finale)

    row.statut = row.statut.__class__.CLOTURE
    from datetime import datetime

    row.date_cloture = datetime.utcnow()
    db.add(row)

    exercice_suivant_id = None
    if cree_exercice_suivant:
        duree = row.date_fin - row.date_debut
        date_debut_suivant = row.date_fin + timedelta(days=1)
        date_fin_suivant = date_debut_suivant + duree

        nouvel_exercice = ExerciceComptable(
            client_id=row.client_id,
            date_debut=date_debut_suivant,
            date_fin=date_fin_suivant,
            statut=row.statut.__class__.NON_DEMARRE,
            origine=row.origine.__class__.REPRIS,
            exercice_precedent_id=row.id,
        )
        db.add(nouvel_exercice)
        db.flush()
        for ligne in solde_suivant:
            db.add(
                SoldeOuverture(
                    exercice_id=nouvel_exercice.id,
                    compte_pcg=ligne.compte_pcg,
                    solde_debit=ligne.solde_debit,
                    solde_credit=ligne.solde_credit,
                    source=SoldeOuverture.__table__.c.source.type.enum_class.CLOTURE_AUTO,
                )
            )
        # Démarrage immédiat de l'exercice suivant avec le solde généré
        domain.demarrer_exercice(
            _to_domain_exercice(nouvel_exercice),
            solde_suivant,
        )
        nouvel_exercice.statut = nouvel_exercice.statut.__class__.EN_COURS
        exercice_suivant_id = nouvel_exercice.id

    db.commit()
    return {
        "exercice": row,
        "exercice_suivant_cree": exercice_suivant_id,
        "nombre_lignes_solde_reporte": len(solde_suivant),
    }


def reouvrir_exercice(db: Session, exercice_id: UUID, role_utilisateur: str) -> ExerciceComptable:
    row = db.get(ExerciceComptable, exercice_id)
    if row is None:
        raise ValueError("Exercice introuvable")

    domain.reouvrir_exercice(_to_domain_exercice(row), role_utilisateur)
    row.statut = row.statut.__class__.EN_COURS
    db.commit()
    db.refresh(row)
    return row
