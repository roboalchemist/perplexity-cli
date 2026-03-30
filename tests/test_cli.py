"""Integration tests for CLI interface."""

import pytest
import subprocess
import sys
import os
from pathlib import Path


class TestCLIIntegration:
    """Integration tests running the CLI as a subprocess."""

    @pytest.fixture
    def script_path(self):
        """Return the path to the perplexity.py script."""
        return Path(__file__).parent.parent / "perplexity.py"

    def test_cli_help(self, script_path):
        """Test that --help flag works."""
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "query" in result.stdout.lower()

    def test_cli_version(self, script_path):
        """Test that CLI can be invoked (basic sanity check)."""
        # This just tests the script is runnable
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_cli_requires_query_argument(self, script_path):
        """Test that CLI requires a query argument."""
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        # argparse should complain about missing required argument

    def test_cli_with_verbose_flag(self, script_path):
        """Test that verbose flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-v"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure (it prints "Invalid api key!" and continues)
        # But verbose flag should be accepted and produce debug output
        assert "DEBUG" in result.stderr or "Invalid api key" in result.stdout

    def test_cli_with_model_flag(self, script_path):
        """Test that model flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-m", "sonar"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_invalid_model(self, script_path):
        """Test that invalid model is rejected."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-m", "invalid-model"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # Invalid model causes an exception which exits with code 1
        assert result.returncode == 1

    def test_cli_with_usage_flag(self, script_path):
        """Test that usage flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-u"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_citations_flag(self, script_path):
        """Test that citations flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-c"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_glow_flag(self, script_path):
        """Test that glow flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-g"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_json_flag(self, script_path):
        """Test that json flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-j"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_plaintext_flag(self, script_path):
        """Test that plaintext flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-p"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_plaintext_long_flag(self, script_path):
        """Test that --plaintext long flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "--plaintext"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_plaintext_flag_in_help(self, script_path):
        """Test that plaintext flag is documented in --help."""
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )
        assert "-p" in result.stdout or "--plaintext" in result.stdout

    def test_cli_with_search_type(self, script_path):
        """Test that search type flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-s", "fast"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_invalid_search_type(self, script_path):
        """Test that invalid search type is rejected."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-s", "invalid"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_cli_with_domain_filter(self, script_path):
        """Test that domain filter flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-d", "github.com"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_recency_filter(self, script_path):
        """Test that recency filter flag is accepted."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-r", "week"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0

    def test_cli_with_invalid_recency_filter(self, script_path):
        """Test that invalid recency filter is rejected."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-r", "invalid"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_cli_without_api_key(self, script_path, monkeypatch):
        """Test that CLI fails gracefully without API key."""
        # Ensure PERPLEXITY_API_KEY is not set
        env = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
        result = subprocess.run(
            [sys.executable, str(script_path), "test"],
            capture_output=True,
            text=True,
            env=env
        )
        assert result.returncode != 0

    def test_cli_multiple_flags(self, script_path):
        """Test that multiple flags can be combined."""
        result = subprocess.run(
            [sys.executable, str(script_path), "test", "-u", "-c", "-g"],
            capture_output=True,
            text=True,
            env={**os.environ, "PERPLEXITY_API_KEY": "fake-key-for-testing"}
        )
        # The CLI returns 0 even on auth failure
        assert "Invalid api key" in result.stdout or result.returncode == 0


class TestMainFunction:
    """Tests for the main() function."""

    def test_main_imports_without_error(self):
        """Test that the main module can be imported."""
        import perplexity
        assert hasattr(perplexity, 'main')

    def test_available_models_is_defined(self):
        """Test that AVAILABLE_MODELS is defined."""
        import perplexity
        assert hasattr(perplexity, 'AVAILABLE_MODELS')
        assert isinstance(perplexity.AVAILABLE_MODELS, list)
        assert len(perplexity.AVAILABLE_MODELS) > 0
