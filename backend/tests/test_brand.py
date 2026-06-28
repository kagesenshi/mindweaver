# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi.testclient import TestClient
from mindweaver.config import settings
import pytest
from pathlib import Path


def test_get_brand_defaults(client: TestClient):
    """
    Test retrieving the brand settings via the public GET /api/v1/_brand endpoint
    with default configuration.
    """
    # Force default settings
    settings.brand_name = "Mindweaver"
    settings.brand_logo = "logo.svg"
    settings.brand_bgcolor = None

    response = client.get("/api/v1/_brand")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Mindweaver"
    assert "<svg" in data["logo"]
    assert data["bgcolor"] is None


def test_get_brand_overrides(client: TestClient, tmp_path):
    """
    Test retrieving the brand settings with custom brand name, logo, and bgcolor.
    """
    # Set custom settings
    settings.brand_name = "Custom Brand"
    settings.brand_bgcolor = "#ff0000"

    # Create a custom temp logo.svg in the resources/assets/ folder
    assets_dir = Path(__file__).parent.parent / "src" / "mindweaver" / "resources" / "assets"
    custom_logo_file = assets_dir / "custom_logo.svg"

    try:
        # Write dummy SVG content
        custom_logo_file.write_text("<svg>Custom Logo</svg>", encoding="utf-8")
        settings.brand_logo = "custom_logo.svg"

        response = client.get("/api/v1/_brand")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Custom Brand"
        assert data["logo"] == "<svg>Custom Logo</svg>"
        assert data["bgcolor"] == "#ff0000"
    finally:
        # Clean up custom logo file
        if custom_logo_file.exists():
            custom_logo_file.unlink()
        # Reset settings
        settings.brand_name = "Mindweaver"
        settings.brand_logo = "logo.svg"
        settings.brand_bgcolor = None


def test_get_brand_logo_fallback(client: TestClient):
    """
    Test retrieving the brand settings when configured brand logo does not exist
    ensuring it falls back to logo.svg.
    """
    settings.brand_name = "Fallback Brand"
    settings.brand_logo = "nonexistent.svg"
    settings.brand_bgcolor = None

    try:
        response = client.get("/api/v1/_brand")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Fallback Brand"
        # Since nonexistent.svg does not exist, it must fallback to logo.svg content
        assert "<svg" in data["logo"]
    finally:
        # Reset settings
        settings.brand_name = "Mindweaver"
        settings.brand_logo = "logo.svg"
        settings.brand_bgcolor = None

