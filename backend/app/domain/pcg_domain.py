"""
Moteur du Plan Comptable Général (PCG) français.

Remplace la simple validation regex (proposition_domain.valider_format_compte_pcg)
par un vrai référentiel : chaque compte a un libellé, une classe, et on peut
chercher par préfixe ou par mot-clé, valider son existence, et suggérer des
comptes proches quand l'IA (ou un humain) propose un compte invalide.

HONNÊTETÉ SUR LE PÉRIMÈTRE : le PCG officiel comporte plusieurs milliers de
comptes (avec toutes les subdivisions). Ce référentiel couvre les comptes les
plus courants pour une TPE/PME (une centaine), organisés pour être étendus
facilement (liste plate compte -> libellé). Pour un usage en production, cette
nomenclature devrait être complétée depuis la nomenclature officielle
(publiée par l'ANC) plutôt que ressaisie à la main.
"""

from dataclasses import dataclass

LIBELLES_CLASSES = {
    1: "Comptes de capitaux",
    2: "Comptes d'immobilisations",
    3: "Comptes de stocks et en-cours",
    4: "Comptes de tiers",
    5: "Comptes financiers",
    6: "Comptes de charges",
    7: "Comptes de produits",
    8: "Comptes spéciaux",
}

# Référentiel des comptes courants — extensible. Clé = compte, valeur = libellé.
NOMENCLATURE_PCG: dict[str, str] = {
    # Classe 1 — Capitaux
    "101000": "Capital social",
    "106100": "Réserve légale",
    "110000": "Report à nouveau (solde créditeur)",
    "119000": "Report à nouveau (solde débiteur)",
    "120000": "Résultat de l'exercice (bénéfice)",
    "129000": "Résultat de l'exercice (perte)",
    "164000": "Emprunts auprès des établissements de crédit",
    # Classe 2 — Immobilisations
    "205000": "Concessions et droits similaires, brevets, licences",
    "213500": "Installations générales, agencements",
    "218300": "Matériel de bureau et informatique",
    "218400": "Mobilier",
    "281830": "Amortissements du matériel de bureau et informatique",
    # Classe 3 — Stocks
    "310000": "Matières premières",
    "370000": "Stocks de marchandises",
    # Classe 4 — Tiers
    "401000": "Fournisseurs",
    "404000": "Fournisseurs d'immobilisations",
    "411000": "Clients",
    "421000": "Personnel — rémunérations dues",
    "431000": "Sécurité sociale",
    "437000": "Autres organismes sociaux",
    "444000": "État — impôt sur les bénéfices",
    "445510": "TVA à décaisser",
    "445620": "TVA déductible sur immobilisations",
    "445660": "TVA déductible sur autres biens et services",
    "445710": "TVA collectée",
    "445830": "Crédit de TVA à reporter",
    "455000": "Associés — comptes courants",
    "467000": "Autres comptes débiteurs ou créditeurs",
    # Classe 5 — Financiers
    "512000": "Banque",
    "530000": "Caisse",
    "580000": "Virements internes",
    # Classe 6 — Charges
    "601000": "Achats de matières premières",
    "606100": "Fournitures non stockables (eau, énergie)",
    "606300": "Fournitures d'entretien et de petit équipement",
    "606400": "Fournitures administratives",
    "607000": "Achats de marchandises",
    "611000": "Sous-traitance générale",
    "613200": "Locations immobilières",
    "613500": "Locations mobilières",
    "615000": "Entretien et réparations",
    "616000": "Primes d'assurance",
    "618200": "Documentation générale",
    "618300": "Documentation technique",
    "621000": "Personnel extérieur à l'entreprise",
    "622600": "Honoraires",
    "622700": "Frais d'actes et de contentieux",
    "623100": "Annonces et insertions publicitaires",
    "624700": "Transports de personnel",
    "625600": "Missions et réceptions",
    "625700": "Réceptions",
    "626000": "Frais postaux et de télécommunications",
    "627000": "Services bancaires",
    "628100": "Cotisations diverses",
    "631000": "Impôts, taxes sur rémunérations",
    "635000": "Autres impôts et taxes",
    "641000": "Rémunérations du personnel",
    "645000": "Charges de sécurité sociale et prévoyance",
    "651000": "Redevances pour concessions, brevets",
    "658000": "Charges diverses de gestion courante",
    "661000": "Charges d'intérêts",
    "681000": "Dotations aux amortissements",
    "695000": "Impôts sur les bénéfices",
    # Classe 7 — Produits
    "701000": "Ventes de produits finis",
    "706000": "Prestations de services",
    "706100": "Prestations de services (activité secondaire)",
    "707000": "Ventes de marchandises",
    "708500": "Ports et frais accessoires facturés",
    "758000": "Produits divers de gestion courante",
    "764000": "Revenus des valeurs mobilières de placement",
    "768000": "Autres produits financiers",
    "775000": "Produits des cessions d'éléments d'actif",
    "791000": "Transferts de charges d'exploitation",
}


@dataclass
class CompteInfo:
    compte_pcg: str
    libelle: str
    classe: int
    libelle_classe: str


class PCGError(Exception):
    pass


def _construire_info(compte_pcg: str, libelle: str) -> CompteInfo:
    classe = int(compte_pcg[0])
    return CompteInfo(compte_pcg, libelle, classe, LIBELLES_CLASSES.get(classe, "Inconnue"))


def compte_existe(compte_pcg: str) -> bool:
    return compte_pcg in NOMENCLATURE_PCG


def obtenir_compte(compte_pcg: str) -> CompteInfo:
    if compte_pcg not in NOMENCLATURE_PCG:
        raise PCGError(f"Compte '{compte_pcg}' inconnu de la nomenclature")
    return _construire_info(compte_pcg, NOMENCLATURE_PCG[compte_pcg])


def rechercher_comptes(terme: str, limite: int = 10) -> list[CompteInfo]:
    """
    Recherche par préfixe numérique (ex: '606' -> tous les comptes 606xxx)
    ou par mot-clé dans le libellé (ex: 'assurance' -> 616000).
    """
    terme = terme.strip().lower()
    resultats: list[CompteInfo] = []

    if terme.isdigit():
        for compte, libelle in NOMENCLATURE_PCG.items():
            if compte.startswith(terme):
                resultats.append(_construire_info(compte, libelle))
    else:
        for compte, libelle in NOMENCLATURE_PCG.items():
            if terme in libelle.lower():
                resultats.append(_construire_info(compte, libelle))

    return sorted(resultats, key=lambda c: c.compte_pcg)[:limite]


def suggerer_comptes_proches(compte_invalide: str, limite: int = 3) -> list[CompteInfo]:
    """
    Quand l'IA (ou un comptable) propose un compte qui n'existe pas dans la
    nomenclature, cherche les comptes existants les plus proches par préfixe
    décroissant (ex: '606305' inconnu -> cherche '6063', puis '606', puis '60').
    """
    for longueur in range(len(compte_invalide) - 1, 1, -1):
        prefixe = compte_invalide[:longueur]
        candidats = [
            _construire_info(c, l) for c, l in NOMENCLATURE_PCG.items() if c.startswith(prefixe)
        ]
        if candidats:
            return sorted(candidats, key=lambda c: c.compte_pcg)[:limite]
    return []


def lister_classe(classe: int) -> list[CompteInfo]:
    if classe not in LIBELLES_CLASSES:
        raise PCGError(f"Classe {classe} invalide (attendu : 1 à 8)")
    return sorted(
        (_construire_info(c, l) for c, l in NOMENCLATURE_PCG.items() if int(c[0]) == classe),
        key=lambda c: c.compte_pcg,
    )
