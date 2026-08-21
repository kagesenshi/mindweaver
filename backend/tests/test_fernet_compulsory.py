# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch
from mindweaver.config import settings
from mindweaver.crypto import EncryptionError


@pytest.mark.asyncio
async def test_lifespan_fails_missing_key():
    """Verify that lifespan fails if the Fernet key is missing."""
    from mindweaver.app import lifespan
    
    with patch.object(settings, "fernet_key", None):
        with pytest.raises(EncryptionError, match="No encryption key configured"):
            async with lifespan(None):
                pass


@pytest.mark.asyncio
async def test_lifespan_fails_invalid_key():
    """Verify that lifespan fails if the Fernet key is invalid."""
    from mindweaver.app import lifespan
    
    with patch.object(settings, "fernet_key", "invalid-key-not-base64-or-short"):
        with pytest.raises(EncryptionError, match="Invalid encryption key"):
            async with lifespan(None):
                pass


def test_celery_worker_init_fails_missing_key():
    """Verify that Celery worker init fails if the Fernet key is missing."""
    from mindweaver.celery_app import check_fernet_on_worker_init
    
    with patch.object(settings, "fernet_key", None):
        with pytest.raises(EncryptionError, match="No encryption key configured"):
            check_fernet_on_worker_init()


def test_celery_beat_init_fails_invalid_key():
    """Verify that Celery beat init fails if the Fernet key is invalid."""
    from mindweaver.celery_app import check_fernet_on_beat_init
    
    with patch.object(settings, "fernet_key", "invalid-key-not-base64-or-short"):
        with pytest.raises(EncryptionError, match="Invalid encryption key"):
            check_fernet_on_beat_init()
