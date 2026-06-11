# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedService
from mindweaver.fw.service import before_create, before_update, redefine_model
from mindweaver.fw.exc import FieldValidationError
from typing import Any
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.primitives import serialization
from pydantic import ValidationError

from .model import SSHKey, SSHKeyConfig


class SSHKeyService(ProjectScopedService[SSHKey]):
    """Service for managing SSH Key pairs."""

    @classmethod
    def model_class(cls) -> type[SSHKey]:
        return SSHKey

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["private_key"]

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + ["private_key", "public_key"]

    @classmethod
    def schema_class(cls) -> type[SSHKey]:
        return redefine_model(
            f"{cls.model_class().__name__}Schema",
            cls.model_class(),
            exclude=["private_key", "public_key"]
        )

    @classmethod
    def immutable_fields(cls) -> list[str]:
        return super().immutable_fields() + ["algorithm", "key_size", "private_key", "public_key"]

    @before_create(before="_handle_redacted_create")
    async def process_keys_create(self, model: SSHKey):
        """
        Processes keys on creation by generating a new key pair using the selected
        algorithm (RSA or Ed25519) and key size (for RSA).
        """
        # Validate metadata first
        try:
            SSHKeyConfig(algorithm=model.algorithm, key_size=model.key_size)
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )

        # Generate keypair
        alg = model.algorithm.lower()
        if alg == "rsa":
            size = model.key_size or 4096
            private_key_obj = rsa.generate_private_key(
                public_exponent=65537,
                key_size=size
            )
            private_pem = private_key_obj.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode("utf-8")
            public_openssh = private_key_obj.public_key().public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            ).decode("utf-8")
        elif alg == "ed25519":
            private_key_obj = ed25519.Ed25519PrivateKey.generate()
            private_pem = private_key_obj.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode("utf-8")
            public_openssh = private_key_obj.public_key().public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            ).decode("utf-8")
        else:
            raise FieldValidationError(
                field_location=["algorithm"],
                message=f"Unsupported algorithm: {model.algorithm}"
            )

        model.private_key = private_pem
        model.public_key = public_openssh

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "algorithm": {
                "order": 3,
                "type": "select",
                "label": "Algorithm",
                "options": [
                    {"label": "RSA", "value": "rsa"},
                    {"label": "Ed25519", "value": "ed25519"},
                ],
            },
            "key_size": {
                "order": 4,
                "type": "select",
                "label": "Key Size (RSA only)",
                "options": [
                    {"label": "2048 bits", "value": 2048},
                    {"label": "4096 bits", "value": 4096},
                ],
            },
        }
