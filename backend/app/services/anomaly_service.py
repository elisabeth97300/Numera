from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.anomaly_domain import Anomalie, EcritureComparable, detecter_doublons_probables
from app.services import ecriture_service


def detecter_anomalies_client(db: Session, client_id: UUID) -> list[Anomalie]:
    """
    Reconstruit une vue comparable des écritures du journal achats/ventes du
    client (tiers = ce qui suit le dernier ' — ' du libellé, montant TTC =
    somme des crédits de l'écriture) puis applique la détection de doublons
    flous. Une vraie modélisation métier gagnerait à stocker le tiers comme
    champ dédié plutôt que de le déduire du libellé — TODO pour l'étape
    suivante une fois le retour des premiers cabinets pilotes obtenu.
    """
    ecritures = ecriture_service.lister_ecritures(db, client_id)

    comparables = []
    for e in ecritures:
        montant_ttc = sum((Decimal(str(l.credit)) for l in e.lignes), Decimal("0"))
        if montant_ttc == 0:
            continue
        tiers = e.libelle.split("—")[-1].strip() if "—" in e.libelle else e.libelle
        comparables.append(EcritureComparable(id=str(e.id), tiers=tiers, montant_ttc=montant_ttc, date_ecriture=e.date_ecriture))

    return detecter_doublons_probables(comparables)
