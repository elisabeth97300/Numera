"""
Logique métier pure du rapprochement bancaire.

Principe : chaque ligne d'un relevé bancaire importé est comparée aux lignes
d'écritures du compte banque (512xxx) pour proposer une correspondance
(lettrage). Comme pour la détection de doublons (anomaly_domain.py), on ne
force JAMAIS un rapprochement automatique en cas d'ambiguïté — une ligne avec
plusieurs candidats possibles est explicitement marquée "à vérifier" pour que
le comptable tranche, plutôt que de risquer un lettrage silencieusement faux.
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum


class StatutRapprochement(str, Enum):
    RAPPROCHE_AUTOMATIQUE = "rapproche_automatique"
    RAPPROCHE_MANUEL = "rapproche_manuel"
    A_VERIFIER = "a_verifier"       # plusieurs candidats possibles, ambigu
    NON_RAPPROCHE = "non_rapproche"  # aucun candidat trouvé


class RapprochementError(Exception):
    """Erreur métier liée au rapprochement bancaire."""


@dataclass
class LigneReleve:
    """Une ligne du relevé bancaire importé. Montant positif = encaissement, négatif = décaissement."""

    id: str
    date: date
    libelle: str
    montant: Decimal


@dataclass
class LigneEcritureBanque:
    """Une ligne d'écriture du compte banque (512xxx), telle qu'enregistrée dans le grand livre."""

    id: str
    date: date
    libelle: str
    debit: Decimal
    credit: Decimal

    def montant_signe(self) -> Decimal:
        """Positif = encaissement (débit du compte banque), négatif = décaissement (crédit)."""
        return self.debit - self.credit


@dataclass
class Rapprochement:
    ligne_releve_id: str
    ligne_ecriture_id: str | None
    statut: StatutRapprochement
    candidats_alternatifs: list[str] = field(default_factory=list)


TOLERANCE_JOURS = 5
TOLERANCE_MONTANT = Decimal("0.01")


def proposer_rapprochements(
    lignes_releve: list[LigneReleve], lignes_ecriture: list[LigneEcritureBanque]
) -> list[Rapprochement]:
    """
    Propose un rapprochement pour chaque ligne du relevé :
    - un seul candidat (même montant à la tolérance près, date proche) -> rapproché automatiquement ;
    - plusieurs candidats mais un seul à la date exacte -> celui-là est retenu ;
    - plusieurs candidats sans date exacte qui les départage -> "à vérifier",
      avec la liste des candidats pour que l'interface les propose au comptable ;
    - aucun candidat -> "non rapproché" (à traiter manuellement ou à
      rapprocher plus tard, une fois l'écriture correspondante saisie).

    Une écriture déjà utilisée pour une ligne de relevé n'est jamais réutilisée
    pour une autre (traitement dans l'ordre du relevé, glouton mais suffisant
    tant que les doublons de montant/date restent rares).
    """
    deja_utilisees: set[str] = set()
    resultats: list[Rapprochement] = []

    for lr in lignes_releve:
        candidats = [
            le
            for le in lignes_ecriture
            if le.id not in deja_utilisees
            and abs(le.montant_signe() - lr.montant) <= TOLERANCE_MONTANT
            and abs((le.date - lr.date).days) <= TOLERANCE_JOURS
        ]

        if len(candidats) == 0:
            resultats.append(Rapprochement(lr.id, None, StatutRapprochement.NON_RAPPROCHE))
            continue

        if len(candidats) == 1:
            deja_utilisees.add(candidats[0].id)
            resultats.append(Rapprochement(lr.id, candidats[0].id, StatutRapprochement.RAPPROCHE_AUTOMATIQUE))
            continue

        candidats_date_exacte = [c for c in candidats if c.date == lr.date]
        if len(candidats_date_exacte) == 1:
            deja_utilisees.add(candidats_date_exacte[0].id)
            resultats.append(
                Rapprochement(lr.id, candidats_date_exacte[0].id, StatutRapprochement.RAPPROCHE_AUTOMATIQUE)
            )
        else:
            resultats.append(
                Rapprochement(
                    lr.id, None, StatutRapprochement.A_VERIFIER, candidats_alternatifs=[c.id for c in candidats]
                )
            )

    return resultats


def valider_lettrage_manuel(rapprochement: Rapprochement, ligne_ecriture_id: str) -> Rapprochement:
    """
    Le comptable choisit manuellement la bonne correspondance parmi les
    candidats (cas 'à vérifier') ou pour une ligne restée non rapprochée.
    """
    if rapprochement.statut == StatutRapprochement.RAPPROCHE_AUTOMATIQUE:
        raise RapprochementError("Cette ligne est déjà rapprochée automatiquement")
    if (
        rapprochement.candidats_alternatifs
        and ligne_ecriture_id not in rapprochement.candidats_alternatifs
    ):
        raise RapprochementError("Cette écriture ne fait pas partie des candidats proposés pour cette ligne")

    return Rapprochement(
        ligne_releve_id=rapprochement.ligne_releve_id,
        ligne_ecriture_id=ligne_ecriture_id,
        statut=StatutRapprochement.RAPPROCHE_MANUEL,
    )


def generer_code_lettrage(index: int) -> str:
    """
    Génère un code de lettrage séquentiel A, B, ..., Z, AA, AB, ... (même
    principe que la numérotation des colonnes d'un tableur). index commence à 0.
    """
    if index < 0:
        raise RapprochementError("L'index de lettrage doit être positif")
    code = ""
    n = index
    while True:
        n, reste = divmod(n, 26)
        code = chr(65 + reste) + code
        if n == 0:
            break
        n -= 1
    return code


@dataclass
class SoldeRapprochement:
    nombre_lignes_releve: int
    nombre_rapprochees: int
    nombre_a_verifier: int
    nombre_non_rapprochees: int

    def taux_rapprochement(self) -> float:
        if self.nombre_lignes_releve == 0:
            return 1.0
        return self.nombre_rapprochees / self.nombre_lignes_releve


def calculer_solde_rapprochement(rapprochements: list[Rapprochement]) -> SoldeRapprochement:
    rapprochees = sum(
        1
        for r in rapprochements
        if r.statut in (StatutRapprochement.RAPPROCHE_AUTOMATIQUE, StatutRapprochement.RAPPROCHE_MANUEL)
    )
    a_verifier = sum(1 for r in rapprochements if r.statut == StatutRapprochement.A_VERIFIER)
    non_rapprochees = sum(1 for r in rapprochements if r.statut == StatutRapprochement.NON_RAPPROCHE)

    return SoldeRapprochement(
        nombre_lignes_releve=len(rapprochements),
        nombre_rapprochees=rapprochees,
        nombre_a_verifier=a_verifier,
        nombre_non_rapprochees=non_rapprochees,
    )


# --- Parsing du fichier CSV de relevé bancaire -----------------------------
# Logique volontairement ici plutôt que dans la couche service : elle ne
# dépend d'aucun framework, uniquement de la stdlib, et représente une vraie
# règle métier (quel format de date/montant on accepte) plutôt qu'un détail
# d'infrastructure.

FORMATS_DATE = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y")


def _parser_date(valeur: str) -> date:
    for fmt in FORMATS_DATE:
        try:
            return datetime.strptime(valeur.strip(), fmt).date()
        except ValueError:
            continue
    raise RapprochementError(f"Format de date non reconnu : '{valeur}'")


def _parser_montant(valeur: str) -> Decimal:
    try:
        return Decimal(valeur.strip().replace(" ", "").replace(",", "."))
    except InvalidOperation as e:
        raise RapprochementError(f"Montant illisible : '{valeur}'") from e


def parser_csv_releve(contenu: bytes) -> list[tuple[date, str, Decimal]]:
    """
    Parse un CSV de relevé bancaire. Format attendu, avec en-tête :
    date;libelle;montant (séparateur ; ou ,, montant en virgule ou point,
    positif = encaissement, négatif = décaissement — format standard export
    banque française). Les lignes illisibles sont ignorées plutôt que de
    faire échouer tout l'import, mais pourraient être remontées à l'UI en v1.1.
    """
    texte = contenu.decode("utf-8-sig", errors="replace")
    if not texte.strip():
        return []

    dialecte = csv.Sniffer().sniff(texte.splitlines()[0])
    lecteur = csv.reader(io.StringIO(texte), dialect=dialecte)

    lignes: list[tuple[date, str, Decimal]] = []
    for i, ligne in enumerate(lecteur):
        if len(ligne) < 3:
            continue
        if i == 0:
            # ligne d'en-tête probable si la 3e colonne n'est pas un nombre
            try:
                _parser_montant(ligne[2])
            except RapprochementError:
                continue
        try:
            date_op = _parser_date(ligne[0])
            libelle = ligne[1].strip()
            montant = _parser_montant(ligne[2])
            lignes.append((date_op, libelle, montant))
        except RapprochementError:
            continue

    return lignes
