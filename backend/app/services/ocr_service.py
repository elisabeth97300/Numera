"""
Service OCR : lit un document (image ou PDF) et en extrait le texte brut puis
des champs structurés (montant, date, tiers, TVA) par des règles simples.

Utilise Tesseract par défaut (gratuit, fonctionne hors ligne). Le paramètre
`moteur` permet de basculer vers Google Vision pour les documents difficiles
(écriture manuscrite, mise en page complexe) sans changer l'appelant.

NOTE IMPORTANTE : ce module nécessite tesseract-ocr installé sur la machine
(cf. Dockerfile du backend) et n'a pas pu être exécuté dans l'environnement
de génération de ce code (pas d'accès réseau ni de binaire tesseract dans ce
sandbox). La logique d'interprétation du résultat brut est en revanche testée
indépendamment dans app/domain/document_domain.py.
"""

import re
from decimal import Decimal, InvalidOperation

from app.domain.document_domain import ChampExtrait, ResultatOCR

# Regex volontairement simples : elles couvrent le cas fréquent d'une facture
# française standard, mais ne remplacent pas un vrai modèle de reconnaissance
# de champs (l'étape 4 / IA comptable affine ensuite avec le LLM).
RE_MONTANT_TTC = re.compile(r"(?:total\s*ttc|net\s*à\s*payer).{0,20}?(\d+[.,]\d{2})", re.IGNORECASE)
RE_TVA = re.compile(r"(?:tva|dont\s*tva).{0,20}?(\d+[.,]\d{2})", re.IGNORECASE)
RE_DATE = re.compile(r"(\d{2}[/\-]\d{2}[/\-]\d{4})")
RE_SIREN = re.compile(r"\b(\d{9})\b")


def _extraire_montant(pattern: re.Pattern, texte: str) -> tuple[str | None, float]:
    match = pattern.search(texte)
    if not match:
        return None, 0.0
    valeur_brute = match.group(1).replace(",", ".")
    try:
        Decimal(valeur_brute)
    except InvalidOperation:
        return None, 0.0
    return valeur_brute, 0.85  # confiance heuristique ; un vrai modèle donnerait un score réel


def analyser_texte(texte_brut: str) -> ResultatOCR:
    """
    Transforme le texte brut sorti de l'OCR en champs structurés. Séparé de
    l'appel Tesseract lui-même pour rester testable sans dépendance native.
    """
    champs: list[ChampExtrait] = []

    montant_ttc, confiance_ttc = _extraire_montant(RE_MONTANT_TTC, texte_brut)
    if montant_ttc:
        champs.append(ChampExtrait("montant_ttc", montant_ttc, confiance_ttc))

    montant_tva, confiance_tva = _extraire_montant(RE_TVA, texte_brut)
    if montant_tva:
        champs.append(ChampExtrait("montant_tva", montant_tva, confiance_tva))

    date_match = RE_DATE.search(texte_brut)
    if date_match:
        champs.append(ChampExtrait("date", date_match.group(1), 0.8))

    siren_match = RE_SIREN.search(texte_brut)
    if siren_match:
        champs.append(ChampExtrait("siren_tiers", siren_match.group(1), 0.75))

    return ResultatOCR(texte_brut=texte_brut, champs=champs)


def lire_document(contenu_binaire: bytes, extension: str, moteur: str = "tesseract") -> ResultatOCR:
    """
    Point d'entrée principal du module OCR. `contenu_binaire` est le fichier
    tel que stocké sur S3 (image ou PDF).

    Moteurs disponibles :
    - "tesseract" : gratuit, hors ligne, précision correcte sur documents nets.
    - "google_vision" : payant à l'usage, meilleure précision sur documents dégradés.
    - "azure_document_intelligence" : extraction structurée de champs de facture
      nativement (montants, dates, lignes) — souvent supérieur pour ce cas d'usage
      précis plutôt qu'un simple texte brut à reparser.
    - "mistral_ocr" : OCR multimodal, alternative européenne, bon rapport précision/coût.
    """
    if moteur == "tesseract":
        texte_brut = _lire_avec_tesseract(contenu_binaire, extension)
        return analyser_texte(texte_brut)
    if moteur == "google_vision":
        texte_brut = _lire_avec_google_vision(contenu_binaire)
        return analyser_texte(texte_brut)
    if moteur == "azure_document_intelligence":
        return _lire_avec_azure_document_intelligence(contenu_binaire)
    if moteur == "mistral_ocr":
        return _lire_avec_mistral_ocr(contenu_binaire)

    raise ValueError(f"Moteur OCR inconnu : {moteur}")


def _lire_avec_tesseract(contenu_binaire: bytes, extension: str) -> str:
    import io

    import pytesseract
    from PIL import Image

    if extension.lower() == "pdf":
        # pdf2image convertit chaque page en image avant OCR ; nécessite
        # poppler-utils installé sur la machine (à ajouter au Dockerfile si
        # l'import de PDF scannés est utilisé en pratique).
        from pdf2image import convert_from_bytes

        pages = convert_from_bytes(contenu_binaire)
        return "\n".join(pytesseract.image_to_string(page, lang="fra") for page in pages)

    image = Image.open(io.BytesIO(contenu_binaire))
    return pytesseract.image_to_string(image, lang="fra")


def _lire_avec_google_vision(contenu_binaire: bytes) -> str:
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=contenu_binaire)
    response = client.text_detection(image=image)
    if response.error.message:
        raise RuntimeError(response.error.message)
    return response.full_text_annotation.text


def _lire_avec_azure_document_intelligence(contenu_binaire: bytes) -> ResultatOCR:
    """
    Azure Document Intelligence a un modèle pré-entraîné "prebuilt-invoice"
    qui extrait directement les champs structurés (pas seulement du texte
    brut) — on peut donc construire un ResultatOCR avec des scores de
    confiance réels renvoyés par Azure, au lieu des scores heuristiques
    utilisés par analyser_texte(). Nécessite AZURE_DOCUMENT_INTELLIGENCE_KEY
    et AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT en configuration (à ajouter à
    app/core/config.py si ce moteur est activé en production).
    """
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    from app.core.config import get_settings

    settings = get_settings()
    client = DocumentIntelligenceClient(
        endpoint=settings.azure_document_intelligence_endpoint,
        credential=AzureKeyCredential(settings.azure_document_intelligence_key),
    )
    poller = client.begin_analyze_document("prebuilt-invoice", contenu_binaire)
    resultat_azure = poller.result()

    champs: list[ChampExtrait] = []
    if resultat_azure.documents:
        doc = resultat_azure.documents[0]
        mapping = {
            "InvoiceTotal": "montant_ttc",
            "TotalTax": "montant_tva",
            "InvoiceDate": "date",
            "VendorName": "tiers",
        }
        for champ_azure, champ_interne in mapping.items():
            f = doc.fields.get(champ_azure)
            if f is not None and f.value is not None:
                champs.append(ChampExtrait(champ_interne, str(f.value), f.confidence or 0.5))

    return ResultatOCR(texte_brut=resultat_azure.content or "", champs=champs)


def _lire_avec_mistral_ocr(contenu_binaire: bytes) -> ResultatOCR:
    """
    Mistral OCR (API mistral.ai) : OCR multimodal renvoyant du texte
    structuré (Markdown). Nécessite MISTRAL_API_KEY. Le texte renvoyé est
    ensuite passé à analyser_texte() comme pour Tesseract/Google Vision, car
    Mistral OCR ne fait pas d'extraction de champs métier nativement
    (contrairement à Azure "prebuilt-invoice").
    """
    import base64

    import httpx

    from app.core.config import get_settings

    settings = get_settings()
    contenu_base64 = base64.b64encode(contenu_binaire).decode("ascii")

    response = httpx.post(
        "https://api.mistral.ai/v1/ocr",
        headers={"Authorization": f"Bearer {settings.mistral_api_key}", "Content-Type": "application/json"},
        json={"model": "mistral-ocr-latest", "document": {"type": "document_base64", "document_base64": contenu_base64}},
        timeout=60.0,
    )
    response.raise_for_status()
    texte_brut = response.json().get("text", "")
    return analyser_texte(texte_brut)
