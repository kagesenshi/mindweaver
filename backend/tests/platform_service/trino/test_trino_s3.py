# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request

from mindweaver.platform_service.trino import TrinoPlatform, TrinoPlatformService
from mindweaver.fw.model import AsyncSession

@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    return request, session

@pytest.mark.asyncio
async def test_trino_s3_region_defaults(mock_service_dependencies):
    """Test that S3 region defaults to us-east-1 when appropriate"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)

    model = TrinoPlatform(
        name="trino-test",
        title="Trino Test",
        project_id=1,
        hms_ids=[10],
    )

    # Mock _resolve_namespace and project
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))

    # Mock HiveMetastorePlatformService
    mock_hms_svc = AsyncMock()
    mock_hms_model = MagicMock()
    mock_hms_model.name = "test-hms"
    mock_hms_model.s3_storage_id = 100
    mock_hms_svc.get.return_value = mock_hms_model
    mock_hms_svc._resolve_namespace.return_value = "hms-ns"
    
    mock_hms_state = MagicMock()
    mock_hms_state.active = True
    mock_hms_state.hms_uri = "thrift://hms-internal:9083"
    mock_hms_svc.platform_state.return_value = mock_hms_state

    # Helper for mocking S3 model
    def get_mock_s3(region, endpoint_url=None):
        m = MagicMock()
        m.region = region
        m.endpoint_url = endpoint_url
        m.access_key = "access"
        m.secret_key = None
        return m

    mock_s3_svc = AsyncMock()
    
    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.S3StorageService.get_service", AsyncMock(return_value=mock_s3_svc)):
        
        # 1. Non-local S3 with region provided
        mock_s3_svc.get.return_value = get_mock_s3("ap-southeast-1")
        vars = await svc.template_vars(model)
        hms_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms")
        assert hms_cat["properties"]["s3.region"] == "ap-southeast-1"

        # 2. Local S3 (has endpoint_url) with region provided -> Should default to us-east-1
        mock_s3_svc.get.return_value = get_mock_s3("ap-southeast-1", "http://minio:9000")
        vars = await svc.template_vars(model)
        hms_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms")
        assert hms_cat["properties"]["s3.region"] == "us-east-1"

        # 3. S3 with no region provided -> Should default to us-east-1
        mock_s3_svc.get.return_value = get_mock_s3("", None)
        vars = await svc.template_vars(model)
        hms_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms")
        assert hms_cat["properties"]["s3.region"] == "us-east-1"
        
        # 4. S3 with only whitespace region -> Should default to us-east-1
        mock_s3_svc.get.return_value = get_mock_s3("   ", None)
        vars = await svc.template_vars(model)
        hms_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms")
        assert hms_cat["properties"]["s3.region"] == "us-east-1"
