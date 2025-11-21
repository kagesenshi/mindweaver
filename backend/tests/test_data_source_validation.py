"""
Test script to demonstrate data source parameter validation.

This script shows examples of valid and invalid data source configurations
and how the validation system handles them.
"""

from mindweaver.service.data_source import (
    APIConfig,
    DBConfig,
    WebScraperConfig,
    FileUploadConfig,
)
from pydantic import ValidationError


def test_api_config_valid():
    """Test valid API configuration."""
    config = APIConfig(base_url="https://api.example.com/v1", api_key="sk_test_123456")
    assert config.base_url == "https://api.example.com/v1"
    assert config.api_key == "sk_test_123456"


def test_api_config_invalid_url():
    """Test API configuration with invalid URL."""
    try:
        config = APIConfig(base_url="not-a-valid-url", api_key="sk_test_123456")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        # Verify that the error is about the URL
        errors = e.errors()
        assert len(errors) > 0
        assert any(error["loc"][0] == "base_url" for error in errors)


def test_api_config_empty_key():
    """Test API configuration with empty API key."""
    try:
        config = APIConfig(base_url="https://api.example.com", api_key="")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        # Verify that the error is about the API key
        errors = e.errors()
        assert len(errors) > 0
        assert any(error["loc"][0] == "api_key" for error in errors)


def test_db_config_valid():
    """Test valid Database configuration."""
    config = DBConfig(host="db.example.com", port=5432, username="admin")
    assert config.host == "db.example.com"
    assert config.port == 5432
    assert config.username == "admin"


def test_db_config_invalid_port():
    """Test Database configuration with invalid port."""
    try:
        config = DBConfig(host="db.example.com", port=99999, username="admin")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        # Verify that the error is about the port
        errors = e.errors()
        assert len(errors) > 0
        assert any(error["loc"][0] == "port" for error in errors)


def test_web_scraper_config_valid():
    """Test valid Web Scraper configuration."""
    config = WebScraperConfig(start_url="https://example.com")
    assert config.start_url == "https://example.com"


def test_web_scraper_config_invalid():
    """Test Web Scraper configuration with invalid URL."""
    try:
        config = WebScraperConfig(start_url="ftp://example.com")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        # Verify that the error is about the URL
        errors = e.errors()
        assert len(errors) > 0
        assert any(error["loc"][0] == "start_url" for error in errors)


def test_file_upload_config():
    """Test File Upload configuration."""
    config = FileUploadConfig()
    assert config.model_dump() == {}


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Data Source Parameter Validation Tests")
    print("=" * 60)

    tests = [
        test_api_config_valid,
        test_api_config_invalid_url,
        test_api_config_empty_key,
        test_db_config_valid,
        test_db_config_invalid_port,
        test_web_scraper_config_valid,
        test_web_scraper_config_invalid,
        test_file_upload_config,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
