"""
Wrapper autour de boto3 pour le stockage des documents sur S3 (ou MinIO en
développement local, compatible avec l'API S3). Isolé dans son propre module
pour que le reste du code ne dépende jamais directement de boto3 — si on
change de fournisseur de stockage un jour, seul ce fichier bouge.
"""

import uuid

import boto3

from app.core.config import get_settings

settings = get_settings()

_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
)


def uploader_fichier(client_id: str, nom_fichier: str, contenu: bytes) -> str:
    """
    Stocke le fichier sous une clé unique (préfixée par le client, pour garder
    une trace de l'organisation même en cas d'inspection directe du bucket) et
    retourne l'URL/clé S3 à conserver dans DocumentSource.fichier_s3_url.
    """
    extension = nom_fichier.rsplit(".", 1)[-1] if "." in nom_fichier else "bin"
    cle = f"{client_id}/{uuid.uuid4()}.{extension}"
    _client.put_object(Bucket=settings.s3_bucket_name, Key=cle, Body=contenu)
    return cle


def url_presignee(cle_s3: str, expiration_secondes: int = 3600) -> str:
    """URL temporaire pour permettre au frontend d'afficher/télécharger le document original."""
    return _client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": cle_s3},
        ExpiresIn=expiration_secondes,
    )
