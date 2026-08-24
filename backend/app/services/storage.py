"""Client-side encrypted storage for raw imported conversation text."""

import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..config import settings


class EncryptedStore:
    def __init__(self, s3_client: Any, kms_key_id: str, kms_client: Any, bucket: str | None = None) -> None:
        self.s3 = s3_client
        self.kms = kms_client
        self.kms_key_id = kms_key_id
        self.bucket = bucket or os.environ["RAW_IMPORTS_BUCKET"]

    def put(self, user_id: str, thread_id: str, raw_text: str) -> tuple[str, bytes]:
        generated = self.kms.generate_data_key(KeyId=self.kms_key_id, KeySpec="AES_256")
        dek = generated["Plaintext"]
        wrapped_dek = generated["CiphertextBlob"]
        nonce = os.urandom(12)
        payload = nonce + AESGCM(dek).encrypt(nonce, raw_text.encode("utf-8"), None)
        blob_key = f"raw/{user_id}/{thread_id}.bin"
        self.s3.put_object(
            Bucket=self.bucket,
            Key=blob_key,
            Body=payload,
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=self.kms_key_id,
        )
        return blob_key, wrapped_dek

    def delete(self, blob_key: str, wrapped_dek: bytes | None = None) -> None:
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=blob_key)
        except Exception as exc:
            raise RuntimeError(
                f"Deletion aborted: blob {blob_key} could not be removed. No deletion receipt issued."
            ) from exc


def configured_store() -> EncryptedStore:
    if not settings.raw_imports_bucket or not settings.kms_key_id:
        raise RuntimeError("Raw import storage is not configured")
    import boto3

    return EncryptedStore(
        s3_client=boto3.client("s3"),
        kms_client=boto3.client("kms"),
        kms_key_id=settings.kms_key_id,
        bucket=settings.raw_imports_bucket,
    )