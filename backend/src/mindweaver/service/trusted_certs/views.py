# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import Depends, HTTPException
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from .service import TrustedCertService
import datetime


@TrustedCertService.model_view("GET", "/_decode")
async def decode_certificate(
    id: int,
    svc: TrustedCertService = Depends(TrustedCertService.get_service),
):
    """
    Decode the certificate details (Subject, Issuer, Validity, etc.)
    and return as JSON.
    """
    cert_record = await svc.get(id)
    if not cert_record:
        raise HTTPException(status_code=404, detail="Trusted certificate not found")

    try:
        cert = x509.load_pem_x509_certificate(
            cert_record.certificate.encode("utf-8"),
            default_backend()
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load or parse PEM certificate: {e}"
        )

    # Helper function to extract name attributes
    def get_name_details(name: x509.Name) -> dict[str, str]:
        details = {}
        for attr in name:
            oid_name = attr.oid._name
            if oid_name:
                details[oid_name] = attr.value
        return details

    subject = get_name_details(cert.subject)
    issuer = get_name_details(cert.issuer)

    now = datetime.datetime.now(datetime.timezone.utc)
    
    # support compatibility for different cryptography versions
    try:
        not_before = cert.not_valid_before_utc
        not_after = cert.not_valid_after_utc
    except AttributeError:
        # fallback for older cryptography versions
        not_before = cert.not_valid_before.replace(tzinfo=datetime.timezone.utc)
        not_after = cert.not_valid_after.replace(tzinfo=datetime.timezone.utc)
        
    is_valid = not_before <= now <= not_after

    return {
        "subject": subject,
        "issuer": issuer,
        "valid_from": not_before.isoformat(),
        "valid_to": not_after.isoformat(),
        "is_valid": is_valid,
        "serial_number": hex(cert.serial_number),
        "version": cert.version.name if hasattr(cert.version, "name") else str(cert.version),
        "signature_algorithm": cert.signature_algorithm_oid._name or str(cert.signature_algorithm_oid),
    }
