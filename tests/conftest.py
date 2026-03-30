"""Pytest configuration and fixtures for perplexity-cli tests."""

import pytest
from unittest.mock import Mock
from io import StringIO
import sys
import os


@pytest.fixture
def mock_api_key(monkeypatch):
    """Fixture to mock the PERPLEXITY_API_KEY environment variable."""
    monkeypatch.setenv("PERPLEXITY_API_KEY", "PLACEHOLDER-API-KEY")
    return "PLACEHOLDER-API-KEY"


@pytest.fixture
def valid_model():
    """Return a valid model name."""
    return "sonar-pro"


@pytest.fixture
def invalid_model():
    """Return an invalid model name."""
    return "invalid-model-name"


@pytest.fixture
def mock_args():
    """Create mock argparse namespace with default values."""
    mock = Mock()
    mock.model = "sonar-pro"
    mock.api_key = "PLACEHOLDER-API-KEY"
    mock.usage = False
    mock.citations = False
    mock.glow = False
    mock.json = False
    mock.plaintext = False
    mock.quiet = False
    mock.silent = False
    mock.search_type = None
    mock.domain_filter = None
    mock.recency_filter = None
    mock.verbose = False
    mock.query = "test query"
    return mock


@pytest.fixture
def mock_api_response():
    """Create a mock API response structure."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a test response from Perplexity AI."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        },
        "citations": [
            "https://example.com/source1",
            "https://example.com/source2"
        ]
    }


@pytest.fixture
def capture_output(monkeypatch):
    """Fixture to capture stdout and stderr."""
    captured = {"stdout": "", "stderr": ""}

    def capture_stdout():
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        yield sys.stdout
        sys.stdout = old_stdout

    def capture_stderr():
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        yield sys.stderr
        sys.stderr = old_stderr

    return captured


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test."""
    # Ensure PERPLEXITY_API_KEY is not set unless explicitly mocked
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)


@pytest.fixture
def sample_query():
    """Return a sample query string."""
    return "What is the capital of France?"


@pytest.fixture
def sample_search_options():
    """Return sample web search options."""
    return {
        "search_type": "pro",
        "search_domain_filter": ["github.com", "stackoverflow.com"],
        "search_recency_filter": "week"
    }
