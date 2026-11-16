"""Private object storage with app-level AES-256-GCM encryption (NFR-08).

Keys are random server-generated names, never user input. Images are encrypted before
they reach any backend, so neither the disk nor a bucket ever holds plaintext.
"""

from __future__ import annotations

import base64
import os
import secrets
from abc import ABC, abstractmethod
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import get_settings


class StorageError(RuntimeError):
    pass


def _key() -> bytes:
    k = base64.b64decode(get_settings().image_encryption_key)
    if len(k) != 32:
        raise StorageError("image encryption key must decode to 32 bytes")
    return k


def encrypt(data: bytes, aad: bytes) -> bytes:
    nonce = os.urandom(12)
    return nonce + AESGCM(_key()).encrypt(nonce, data, aad)


def decrypt(blob: bytes, aad: bytes) -> bytes:
    return AESGCM(_key()).decrypt(blob[:12], blob[12:], aad)


def new_key(prefix: str) -> str:
    return f"{prefix}/{secrets.token_hex(16)}"


class Backend(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes) -> None: ...
    @abstractmethod
    def get(self, key: str) -> bytes: ...
    @abstractmethod
    def delete(self, key: str) -> None: ...
    @abstractmethod
    def exists(self, key: str) -> bool: ...


class LocalBackend(Backend):
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if self.root not in p.parents:
            raise StorageError("invalid key")
        return p

    def put(self, key, data):
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_bytes(data)
        os.chmod(tmp, 0o600)
        tmp.replace(p)

    def get(self, key):
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as e:
            raise StorageError("not found") from e

    def delete(self, key):
        self._path(key).unlink(missing_ok=True)

    def exists(self, key):
        return self._path(key).exists()


class S3Backend(Backend):  # MinIO / S3. Not exercised in this repo's test environment.
    def __init__(self):
        import boto3

        s = get_settings()
        self.bucket = s.s3_bucket
        self.c = boto3.client("s3", endpoint_url=s.s3_endpoint, aws_access_key_id=s.s3_access_key,
                              aws_secret_access_key=s.s3_secret_key)

    def put(self, key, data):
        self.c.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get(self, key):
        try:
            return self.c.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except Exception as e:
            raise StorageError("not found") from e

    def delete(self, key):
        self.c.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key):
        try:
            self.c.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


_backend: Backend | None = None


def backend() -> Backend:
    global _backend
    if _backend is None:
        s = get_settings()
        _backend = S3Backend() if s.storage_backend == "s3" else LocalBackend(s.storage_dir)
    return _backend


def reset_backend() -> None:
    global _backend
    _backend = None


def put_encrypted(prefix: str, data: bytes) -> str:
    key = new_key(prefix)
    backend().put(key, encrypt(data, key.encode()))
    return key


def get_decrypted(key: str) -> bytes:
    return decrypt(backend().get(key), key.encode())
