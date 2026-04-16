"""Tests for config loading and history logging (PC-43, PC-44)."""

import json
import os
import socket
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory so perplexity module is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import perplexity
from perplexity import load_config, make_slug, write_history, CONFIG_DIR


# ---------------------------------------------------------------------------
# load_config tests (PC-43)
# ---------------------------------------------------------------------------

class TestLoadConfig:
    """Tests for the load_config() function."""

    def test_returns_empty_dict_when_file_missing(self, tmp_path, monkeypatch):
        """Missing config file returns empty dict without raising."""
        monkeypatch.setattr(perplexity, "CONFIG_FILE", str(tmp_path / "nonexistent.toml"))
        result = load_config()
        assert result == {}

    def test_loads_history_enabled_true(self, tmp_path, monkeypatch):
        """history_enabled = true is read correctly."""
        cfg = tmp_path / "config.toml"
        cfg.write_text("history_enabled = true\n")
        monkeypatch.setattr(perplexity, "CONFIG_FILE", str(cfg))
        result = load_config()
        assert result.get("history_enabled") is True

    def test_loads_history_enabled_false(self, tmp_path, monkeypatch):
        """history_enabled = false is read correctly."""
        cfg = tmp_path / "config.toml"
        cfg.write_text("history_enabled = false\n")
        monkeypatch.setattr(perplexity, "CONFIG_FILE", str(cfg))
        result = load_config()
        assert result.get("history_enabled") is False

    def test_loads_default_format_json(self, tmp_path, monkeypatch):
        """default_format = "json" is read correctly."""
        cfg = tmp_path / "config.toml"
        cfg.write_text('default_format = "json"\n')
        monkeypatch.setattr(perplexity, "CONFIG_FILE", str(cfg))
        result = load_config()
        assert result.get("default_format") == "json"

    def test_malformed_toml_returns_empty_dict(self, tmp_path, monkeypatch):
        """Malformed TOML silently returns empty dict."""
        cfg = tmp_path / "config.toml"
        cfg.write_text("this is not valid toml = = = [\n")
        monkeypatch.setattr(perplexity, "CONFIG_FILE", str(cfg))
        result = load_config()
        assert result == {}

    def test_empty_file_returns_empty_dict(self, tmp_path, monkeypatch):
        """Empty config file returns empty dict."""
        cfg = tmp_path / "config.toml"
        cfg.write_text("")
        monkeypatch.setattr(perplexity, "CONFIG_FILE", str(cfg))
        result = load_config()
        assert result == {}

    def test_multiple_keys(self, tmp_path, monkeypatch):
        """Multiple keys are all loaded."""
        cfg = tmp_path / "config.toml"
        cfg.write_text('history_enabled = true\ndefault_format = "plaintext"\n')
        monkeypatch.setattr(perplexity, "CONFIG_FILE", str(cfg))
        result = load_config()
        assert result.get("history_enabled") is True
        assert result.get("default_format") == "plaintext"


# ---------------------------------------------------------------------------
# make_slug tests (PC-44)
# ---------------------------------------------------------------------------

class TestMakeSlug:
    """Tests for the make_slug() helper."""

    def test_basic_query(self):
        """Simple words produce a hyphenated slug."""
        assert make_slug("hello world") == "hello-world"

    def test_special_chars_removed(self):
        """Special characters are replaced with hyphens."""
        slug = make_slug("what is AI?! seriously.")
        assert re.match(r"^[a-zA-Z0-9-]+$", slug)

    def test_slug_truncated_to_40(self):
        """Slug is at most 40 characters."""
        long = "a" * 100
        assert len(make_slug(long)) <= 40

    def test_empty_query(self):
        """Empty query produces empty or minimal slug."""
        result = make_slug("")
        assert isinstance(result, str)

    def test_leading_trailing_hyphens_stripped(self):
        """Leading/trailing hyphens are stripped."""
        slug = make_slug("---hello---")
        assert not slug.startswith("-")
        assert not slug.endswith("-")


import re  # noqa: E402 (needed for TestMakeSlug)


# ---------------------------------------------------------------------------
# write_history tests (PC-44)
# ---------------------------------------------------------------------------

class TestWriteHistory:
    """Tests for the write_history() function."""

    def _make_tmp_config_dir(self, tmp_path, monkeypatch):
        """Point CONFIG_DIR to a temp directory."""
        monkeypatch.setattr(perplexity, "CONFIG_DIR", str(tmp_path))
        return tmp_path

    def test_history_not_written_when_disabled(self, tmp_path, monkeypatch):
        """No file is created when history_enabled=False."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        write_history("query", {"query": "test"}, {"result": "ok"}, 100,
                      history_enabled=False, no_history=False)
        history_dir = tmp_path / "history"
        assert not history_dir.exists()

    def test_history_not_written_when_no_history_flag(self, tmp_path, monkeypatch):
        """No file is created when no_history=True even if enabled."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        write_history("query", {"query": "test"}, {"result": "ok"}, 100,
                      history_enabled=True, no_history=True)
        history_dir = tmp_path / "history"
        assert not history_dir.exists()

    def test_history_written_when_enabled(self, tmp_path, monkeypatch):
        """A JSON file is created when history_enabled=True."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        write_history("query", {"query": "test query"}, {"choices": []}, 123,
                      history_enabled=True, no_history=False)
        history_files = list(tmp_path.rglob("*.json"))
        assert len(history_files) == 1

    def test_history_file_contains_correct_fields(self, tmp_path, monkeypatch):
        """History JSON contains all required fields."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        params = {"query": "test query", "model": "sonar-pro"}
        response = {"choices": [{"message": {"content": "answer"}}]}
        write_history("query", params, response, 456,
                      history_enabled=True, no_history=False)
        history_files = list(tmp_path.rglob("*.json"))
        assert len(history_files) == 1
        data = json.loads(history_files[0].read_text())
        assert "timestamp" in data
        assert "hostname" in data
        assert data["command"] == "query"
        assert data["params"]["query"] == "test query"
        assert data["latency_ms"] == 456
        assert data["response"] == response

    def test_history_file_api_key_scrubbed(self, tmp_path, monkeypatch):
        """api_key is removed from params before writing."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        params = {"query": "test", "api_key": "secret-key-123"}
        write_history("query", params, {}, 10,
                      history_enabled=True, no_history=False)
        history_files = list(tmp_path.rglob("*.json"))
        data = json.loads(history_files[0].read_text())
        assert "api_key" not in data["params"]
        assert "query" in data["params"]

    def test_history_path_format(self, tmp_path, monkeypatch):
        """History files land in history/<year>/<month>/<day>/."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        write_history("query", {"query": "test"}, {}, 10,
                      history_enabled=True, no_history=False)
        history_files = list(tmp_path.rglob("*.json"))
        assert len(history_files) == 1
        # Path should be: <CONFIG_DIR>/history/<year>/<month>/<day>/<filename>
        parts = history_files[0].relative_to(tmp_path).parts
        assert parts[0] == "history"
        assert len(parts) == 5  # history / year / month / day / filename.json

    def test_history_filename_contains_slug_and_hostname(self, tmp_path, monkeypatch):
        """Filename includes slug and sanitized hostname."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        write_history("query", {"query": "my test query"}, {}, 10,
                      history_enabled=True, no_history=False)
        history_files = list(tmp_path.rglob("*.json"))
        filename = history_files[0].name
        hostname = socket.gethostname()
        safe_host = re.sub(r"[^a-zA-Z0-9._-]", "-", hostname)
        assert safe_host in filename
        assert "my-test-query" in filename

    def test_history_prints_path_to_stderr(self, tmp_path, monkeypatch, capsys):
        """write_history prints [history] <path> to stderr."""
        self._make_tmp_config_dir(tmp_path, monkeypatch)
        write_history("query", {"query": "test"}, {}, 10,
                      history_enabled=True, no_history=False)
        captured = capsys.readouterr()
        assert "[history]" in captured.err


# ---------------------------------------------------------------------------
# Integration: --no-history CLI flag (PC-44)
# ---------------------------------------------------------------------------

class TestNoHistoryFlag:
    """Tests that --no-history is wired through main() correctly."""

    def test_no_history_attribute_set_on_args(self):
        """Perplexity.__init__ reads no_history from args."""
        mock_args = Mock()
        mock_args.model = "sonar-pro"
        mock_args.api_key = "test-key"
        mock_args.usage = False
        mock_args.citations = False
        mock_args.glow = False
        mock_args.json = False
        mock_args.fields = None
        mock_args.jq = None
        mock_args.plaintext = False
        mock_args.quiet = False
        mock_args.silent = False
        mock_args.output = None
        mock_args.search_type = None
        mock_args.domain_filter = None
        mock_args.recency_filter = None
        mock_args.no_history = True
        mock_args.history_enabled = True

        p = perplexity.Perplexity(mock_args)
        assert p.no_history is True
        assert p.history_enabled is True

    def test_history_enabled_defaults_false_when_not_in_args(self):
        """history_enabled defaults to False when attr absent from args."""
        mock_args = Mock(spec=[
            "model", "api_key", "usage", "citations", "glow", "json",
            "fields", "jq", "plaintext", "quiet", "silent", "output",
            "search_type", "domain_filter", "recency_filter",
        ])
        mock_args.model = "sonar-pro"
        mock_args.api_key = "test-key"
        mock_args.usage = False
        mock_args.citations = False
        mock_args.glow = False
        mock_args.json = False
        mock_args.fields = None
        mock_args.jq = None
        mock_args.plaintext = False
        mock_args.quiet = False
        mock_args.silent = False
        mock_args.output = None
        mock_args.search_type = None
        mock_args.domain_filter = None
        mock_args.recency_filter = None

        p = perplexity.Perplexity(mock_args)
        assert p.history_enabled is False
        assert p.no_history is False

    def test_get_response_calls_write_history_when_enabled(self, tmp_path, monkeypatch):
        """get_response calls write_history on success when history enabled."""
        monkeypatch.setattr(perplexity, "CONFIG_DIR", str(tmp_path))

        mock_args = Mock()
        mock_args.model = "sonar-pro"
        mock_args.api_key = "test-key"
        mock_args.usage = False
        mock_args.citations = False
        mock_args.glow = False
        mock_args.json = False
        mock_args.fields = None
        mock_args.jq = None
        mock_args.plaintext = False
        mock_args.quiet = False
        mock_args.silent = False
        mock_args.output = None
        mock_args.search_type = None
        mock_args.domain_filter = None
        mock_args.recency_filter = None
        mock_args.no_history = False
        mock_args.history_enabled = True

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "answer"}}],
            "citations": [],
            "usage": {},
        }

        with patch("perplexity.requests.post", return_value=mock_response):
            p = perplexity.Perplexity(mock_args)
            p.get_response("test query")

        history_files = list(tmp_path.rglob("*.json"))
        assert len(history_files) == 1

    def test_get_response_skips_write_history_when_no_history(self, tmp_path, monkeypatch):
        """get_response does not write history when no_history=True."""
        monkeypatch.setattr(perplexity, "CONFIG_DIR", str(tmp_path))

        mock_args = Mock()
        mock_args.model = "sonar-pro"
        mock_args.api_key = "test-key"
        mock_args.usage = False
        mock_args.citations = False
        mock_args.glow = False
        mock_args.json = False
        mock_args.fields = None
        mock_args.jq = None
        mock_args.plaintext = False
        mock_args.quiet = False
        mock_args.silent = False
        mock_args.output = None
        mock_args.search_type = None
        mock_args.domain_filter = None
        mock_args.recency_filter = None
        mock_args.no_history = True
        mock_args.history_enabled = True

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "answer"}}],
            "citations": [],
            "usage": {},
        }

        with patch("perplexity.requests.post", return_value=mock_response):
            p = perplexity.Perplexity(mock_args)
            p.get_response("test query")

        history_files = list(tmp_path.rglob("*.json"))
        assert len(history_files) == 0
