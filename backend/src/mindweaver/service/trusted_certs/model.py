# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedNamedBase
from sqlmodel import Field
from pydantic import BaseModel, field_validator


class TrustedCertConfig(BaseModel):
    """Configuration schema for validating trusted certificates."""

    certificate: str

    @field_validator("certificate")
    @classmethod
    def validate_certificate(cls, v: str) -> str:
        """Validate that the certificate is in valid PEM format."""
        cert = v.strip()
        if not cert.startswith("-----BEGIN CERTIFICATE-----") or not cert.endswith("-----END CERTIFICATE-----"):
            raise ValueError("Certificate must be a valid PEM-formatted certificate starting with -----BEGIN CERTIFICATE----- and ending with -----END CERTIFICATE-----")
        return cert


class TrustedCert(ProjectScopedNamedBase, table=True):
    """Database model representing a trusted certificate in a project."""
    __tablename__ = "mw_trusted_cert"

    certificate: str = Field(nullable=False)
