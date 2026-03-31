"""Unit tests for validator classes."""

import pytest
from perplexity import ModelValidator, ApiKeyValidator, AVAILABLE_MODELS
from unittest.mock import patch
import os


class TestModelValidator:
    """Tests for ModelValidator class."""

    def test_validate_with_valid_model(self, valid_model):
        """Test validation returns True for valid models."""
        assert ModelValidator.validate(valid_model) is True

    def test_validate_with_invalid_model(self, invalid_model):
        """Test validation returns False for invalid models."""
        assert ModelValidator.validate(invalid_model) is False

    def test_validate_all_available_models(self):
        """Test that all models in AVAILABLE_MODELS are valid."""
        for model in AVAILABLE_MODELS:
            assert ModelValidator.validate(model) is True, f"{model} should be valid"

    def test_validate_case_sensitive(self):
        """Test that model validation is case-sensitive."""
        assert ModelValidator.validate("sonar-pro") is True
        assert ModelValidator.validate("SONAR-PRO") is False
        assert ModelValidator.validate("Sonar-Pro") is False

    def test_get_available_models(self):
        """Test that get_AVAILABLE_MODELS returns the full list."""
        models = ModelValidator.get_AVAILABLE_MODELS()
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(model, str) for model in models)

    def test_available_models_contains_expected_models(self):
        """Test that expected models are in the list."""
        models = ModelValidator.get_AVAILABLE_MODELS()
        expected_models = ["sonar-pro", "sonar", "sonar-deep-research", "sonar-reasoning-pro"]
        for model in expected_models:
            assert model in models, f"{model} should be in available models"


class TestApiKeyValidator:
    """Tests for ApiKeyValidator class."""

    def test_get_api_key_from_system_when_set(self, monkeypatch):
        """Test retrieving API key when environment variable is set."""
        test_key = "test-key-placeholder"
        monkeypatch.setenv("PERPLEXITY_API_KEY", test_key)
        assert ApiKeyValidator.get_api_key_from_system() == test_key

    def test_get_api_key_from_system_when_not_set(self, monkeypatch):
        """Test retrieving API key when environment variable is not set."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        assert ApiKeyValidator.get_api_key_from_system() is None

    def test_get_api_key_from_system_empty_string(self, monkeypatch):
        """Test retrieving API key when environment variable is empty string."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "")
        # Empty string is still a valid value, not None
        assert ApiKeyValidator.get_api_key_from_system() == ""

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "patched-api-key"}, clear=False)
    def test_get_api_key_with_patch(self):
        """Test retrieving API key using patch.dict."""
        assert ApiKeyValidator.get_api_key_from_system() == "patched-api-key"
