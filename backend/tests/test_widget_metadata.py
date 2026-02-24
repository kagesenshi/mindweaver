# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi.testclient import TestClient
from mindweaver.service.s3_storage import S3StorageService
import pytest


@pytest.mark.asyncio
async def test_widget_metadata_generation(client: TestClient):
    response = client.get("/api/v1/s3_storages/_create-form")
    assert response.status_code == 200
    data = response.json()
    widgets = data["data"]["widgets"]

    # Preferred Defaults
    # project_id (order 0, span 1)
    assert widgets["project_id"]["order"] == 0
    assert widgets["project_id"]["column_span"] == 1

    # name (order 1, span 1)
    assert widgets["name"]["order"] == 1
    assert widgets["name"]["column_span"] == 1

    # title (order 2, span 2)
    assert widgets["title"]["order"] == 2
    assert widgets["title"]["column_span"] == 2

    # Other fields
    assert widgets["endpoint_url"]["order"] == 3
    assert widgets["verify_ssl"]["order"] == 4
    assert widgets["region"]["order"] == 5
    assert widgets["access_key"]["order"] == 6
    assert widgets["secret_key"]["order"] == 7
