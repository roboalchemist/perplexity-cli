"""Unit tests for Perplexity API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from perplexity import Perplexity, InvalidSelectedModelException, ApiKeyNotFoundException
import json
import requests


class TestPerplexityInit:
    """Tests for Perplexity class initialization."""

    def test_init_with_valid_model_and_api_key(self, mock_args):
        """Test successful initialization with valid model and API key."""
        perp = Perplexity(mock_args)
        assert perp.setup.model == "sonar-pro"
        assert perp.setup.api_key == "test-api-key"
        assert perp.setup.usage is False
        assert perp.setup.citations is False

    def test_init_with_invalid_model_raises_exception(self, mock_args, invalid_model):
        """Test that invalid model raises InvalidSelectedModelException."""
        mock_args.model = invalid_model
        with pytest.raises(InvalidSelectedModelException) as exc_info:
            Perplexity(mock_args)
        assert "Invalid model" in str(exc_info.value)

    def test_init_without_api_key_and_no_env_var(self, mock_args, monkeypatch):
        """Test that missing API key raises ApiKeyNotFoundException."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        mock_args.api_key = None
        with pytest.raises(ApiKeyNotFoundException):
            Perplexity(mock_args)

    def test_init_uses_env_var_when_api_key_not_provided(self, mock_args, mock_api_key):
        """Test that environment variable is used when API key arg is None."""
        mock_args.api_key = None
        perp = Perplexity(mock_args)
        assert perp.setup.api_key == mock_api_key

    def test_init_with_search_options(self, mock_args):
        """Test initialization with search options."""
        mock_args.search_type = "pro"
        mock_args.domain_filter = "github.com,stackoverflow.com"
        mock_args.recency_filter = "week"
        perp = Perplexity(mock_args)
        assert perp.search_type == "pro"
        assert perp.domain_filter == "github.com,stackoverflow.com"
        assert perp.recency_filter == "week"

    def test_init_with_glow_mode(self, mock_args):
        """Test initialization with glow mode enabled."""
        mock_args.glow = True
        perp = Perplexity(mock_args)
        assert perp.use_glow is True

    def test_init_with_json_output(self, mock_args):
        """Test initialization with JSON output enabled."""
        mock_args.json = True
        perp = Perplexity(mock_args)
        assert perp.json_output is True

    def test_init_with_plaintext_flag(self, mock_args):
        """Test initialization with plaintext flag enabled."""
        mock_args.plaintext = True
        perp = Perplexity(mock_args)
        assert perp.plaintext is True

    def test_init_with_usage_flag(self, mock_args):
        """Test initialization with usage flag enabled."""
        mock_args.usage = True
        perp = Perplexity(mock_args)
        assert perp.setup.usage is True

    def test_init_with_citations_flag(self, mock_args):
        """Test initialization with citations flag enabled."""
        mock_args.citations = True
        perp = Perplexity(mock_args)
        assert perp.setup.citations is True


class TestPerplexityGetResponse:
    """Tests for Perplexity.get_response method."""

    @patch('perplexity.requests.post')
    def test_get_response_success(self, mock_post, mock_args, mock_api_response):
        """Test successful API response handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        perp = Perplexity(mock_args)
        # This should not raise any exception
        perp.get_response("test query")

    @patch('perplexity.requests.post')
    def test_get_response_with_web_search_options(self, mock_post, mock_args):
        """Test that web search options are included in request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}],
            "citations": [],
            "usage": {}
        }
        mock_post.return_value = mock_response

        mock_args.search_type = "pro"
        mock_args.domain_filter = "github.com"
        mock_args.recency_filter = "week"

        perp = Perplexity(mock_args)
        perp.get_response("test query")

        # Verify the request was made with correct data
        call_args = mock_post.call_args
        query_data = json.loads(call_args[1]['data'])
        assert 'web_search_options' in query_data
        assert query_data['web_search_options']['search_type'] == 'pro'
        assert query_data['web_search_options']['search_domain_filter'] == ['github.com']
        assert query_data['web_search_options']['search_recency_filter'] == 'week'

    @patch('perplexity.requests.post')
    def test_get_response_401_unauthorized(self, mock_post, mock_args, capsys):
        """Test handling of 401 Unauthorized response."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        assert "Invalid api key" in captured.err  # Error messages go to stderr

    @patch('perplexity.requests.post')
    def test_get_response_non_200_status(self, mock_post, mock_args):
        """Test handling of non-200, non-401 responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        perp = Perplexity(mock_args)
        # Should handle gracefully without crashing
        perp.get_response("test query")

    @patch('perplexity.requests.post')
    def test_get_response_json_output(self, mock_post, mock_args, mock_api_response, capsys):
        """Test JSON output mode."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        mock_args.json = True
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        # Should output JSON
        assert '"choices"' in captured.out
        assert '"usage"' in captured.out

    @patch('perplexity.requests.post')
    def test_get_response_domain_filter_parsing(self, mock_post, mock_args):
        """Test that domain filter is correctly parsed from comma-separated string."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}],
            "citations": [],
            "usage": {}
        }
        mock_post.return_value = mock_response

        mock_args.domain_filter = "github.com, stackoverflow.com, reddit.com"
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        call_args = mock_post.call_args
        query_data = json.loads(call_args[1]['data'])
        assert query_data['web_search_options']['search_domain_filter'] == [
            'github.com',
            'stackoverflow.com',
            'reddit.com'
        ]


class TestPerplexityOutputMethods:
    """Tests for Perplexity output formatting methods."""

    @patch('perplexity.requests.post')
    def test_show_usage_with_glow(self, mock_post, mock_args, mock_api_response, capsys):
        """Test usage display with glow mode."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        mock_args.usage = True
        mock_args.glow = True
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        assert "# Tokens" in captured.err  # Usage stats go to stderr

    @patch('perplexity.requests.post')
    def test_show_citations_with_glow(self, mock_post, mock_args, mock_api_response, capsys):
        """Test citations display with glow mode."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        mock_args.citations = True
        mock_args.glow = True
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        assert "# Citations" in captured.err  # Citations go to stderr

    @patch('perplexity.requests.post')
    def test_show_content_with_glow(self, mock_post, mock_args, mock_api_response, capsys):
        """Test content display with glow mode."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        mock_args.glow = True
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        assert "# Content" in captured.err  # Content header goes to stderr

    @patch('perplexity.requests.post')
    def test_show_usage_plaintext_tsv(self, mock_post, mock_args, mock_api_response, capsys):
        """Test usage display in plaintext TSV format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        mock_args.usage = True
        mock_args.plaintext = True
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        # Each line should be key<tab>value with no prefix label
        assert "prompt_tokens\t" in captured.err
        assert "completion_tokens\t" in captured.err
        assert "total_tokens\t" in captured.err
        assert "# Tokens" not in captured.err  # No glow header in plaintext

    @patch('perplexity.requests.post')
    def test_show_citations_plaintext_tsv(self, mock_post, mock_args, mock_api_response, capsys):
        """Test citations display in plaintext TSV format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        mock_args.citations = True
        mock_args.plaintext = True
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        # URLs should be printed directly, one per line
        assert "https://example.com/source1" in captured.err
        assert "https://example.com/source2" in captured.err
        assert "# Citations" not in captured.err  # No glow header in plaintext

    @patch('perplexity.requests.post')
    def test_show_content_plaintext_no_ansi(self, mock_post, mock_args, mock_api_response, capsys):
        """Test content display in plaintext outputs raw content with no ANSI codes."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_post.return_value = mock_response

        mock_args.plaintext = True
        perp = Perplexity(mock_args)
        perp.get_response("test query")

        captured = capsys.readouterr()
        # Content goes to stdout; no ANSI color prefix in stderr
        assert "This is a test response from Perplexity AI." in captured.out
        # No ANSI escape sequences in output
        assert "\033[" not in captured.out
        assert "\033[" not in captured.err
