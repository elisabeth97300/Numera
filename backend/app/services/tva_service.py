from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.tva_domain import LigneTVA, preparer_tva
from app.services.reporting_service import _mouvements_domaine  # réutilise la même agrégation que la balance

# Comptes de TVA standards du PCG français : 44571 (collectée), 445660/445620 (déductible).
PREFIXE_TVA_COLLECTEE = "4457"
PREFIXE_TVA_DEDUCTIBLE = "4456"


def obtenir_preparation_tva(db: Session, exercice_id: UUID, taux_par_defaut: str = "20"):
    """
    Version simplifiée du MVP : le taux de TVA n'étant pas encore stocké par
    ligne d'écriture (cf. modèle LigneEcriture actuel), toutes les lignes de
    TVA détectées par préfixe de compte sont ventilées sous un taux unique
    renseigné manuellement. À affiner une fois qu'un champ `taux_tva` est
    ajouté à LigneEcriture (amélioration naturelle une fois ce module testé
    avec un cabinet pilote).
    """
    from decimal import Decimal

    mouvements = _mouvements_domaine(db, exercice_id)
    lignes_tva = []
    for m in mouvements:
        if m.compte_pcg.startswith(PREFIXE_TVA_COLLECTEE) and m.credit > 0:
            lignes_tva.append(
                LigneTVA(m.compte_pcg, Decimal(taux_par_defaut), Decimal("0"), m.credit, "collectee")
            )
        elif m.compte_pcg.startswith(PREFIXE_TVA_DEDUCTIBLE) and m.debit > 0:
            lignes_tva.append(
                LigneTVA(m.compte_pcg, Decimal(taux_par_defaut), Decimal("0"), m.debit, "deductible")
            )

    return preparer_tva(lignes_tva)
