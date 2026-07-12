"""
Vue "graphe comptable" : projette les relations Client -> Document ->
Proposition -> Écriture -> Compte en nœuds/arêtes exploitables par une
visualisation (ex: react-flow côté frontend).

HONNÊTETÉ SUR LE PÉRIMÈTRE : ce n'est PAS une base de données en graphe
(Neo4j ou équivalent) — les relations existent déjà nativement dans
PostgreSQL via les clés étrangères. Ce service se contente de les projeter
sous une forme graphe pour l'affichage et, potentiellement, pour qu'un LLM
"raisonne" dessus en recevant un contexte structuré plutôt qu'une suite de
tables. Une vraie base graphe deviendrait utile si le volume de requêtes de
type "chemin entre deux entités" devenait significatif — pas le cas pour un
MVP.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import DocumentSource
from app.models.ecriture import Ecriture, LigneEcriture
from app.models.proposition import PropositionIA


def construire_graphe_client(db: Session, client_id: UUID) -> dict:
    noeuds = [{"id": f"client:{client_id}", "type": "client", "label": "Dossier client"}]
    aretes = []

    documents = db.scalars(select(DocumentSource).where(DocumentSource.client_id == client_id)).all()
    for d in documents:
        noeuds.append({"id": f"document:{d.id}", "type": "document", "label": d.type_document.value})
        aretes.append({"source": f"client:{client_id}", "target": f"document:{d.id}", "relation": "possede"})

        propositions = db.scalars(select(PropositionIA).where(PropositionIA.document_source_id == d.id)).all()
        for p in propositions:
            noeud_prop = f"proposition:{p.id}"
            noeuds.append({"id": noeud_prop, "type": "proposition", "label": f"{p.tiers_propose} ({p.compte_propose})"})
            aretes.append({"source": f"document:{d.id}", "target": noeud_prop, "relation": "genere"})

            if p.ecriture_id:
                noeud_ecriture = f"ecriture:{p.ecriture_id}"
                aretes.append({"source": noeud_prop, "target": noeud_ecriture, "relation": "validee_en"})

    ecritures = db.scalars(select(Ecriture).where(Ecriture.client_id == client_id)).all()
    comptes_vus = set()
    for e in ecritures:
        noeud_ecriture = f"ecriture:{e.id}"
        if not any(n["id"] == noeud_ecriture for n in noeuds):
            noeuds.append({"id": noeud_ecriture, "type": "ecriture", "label": e.libelle})

        for ligne in e.lignes:
            noeud_compte = f"compte:{ligne.compte_pcg}"
            if ligne.compte_pcg not in comptes_vus:
                noeuds.append({"id": noeud_compte, "type": "compte", "label": ligne.compte_pcg})
                comptes_vus.add(ligne.compte_pcg)
            aretes.append(
                {
                    "source": noeud_ecriture,
                    "target": noeud_compte,
                    "relation": "debit" if ligne.debit and float(ligne.debit) > 0 else "credit",
                }
            )

    return {"noeuds": noeuds, "aretes": aretes}
