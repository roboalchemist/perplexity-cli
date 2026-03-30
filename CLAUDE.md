# perplexity-cli — CLAUDE.md

## Project Overview

A single-file Python CLI tool that wraps the [Perplexity AI API](https://docs.perplexity.ai/) (`api.perplexity.ai/chat/completions`). Users query Perplexity's web-grounded LLMs from the terminal and get formatted responses with optional citations, token usage stats, and search controls.

- **Public repo**: `~/github/perplexity-cli` → `github.com/roboalchemist/perplexity-cli`
- **Homebrew tap**: `roboalchemist/tap/perplexity-cli` (public tap at `github.com/roboalchemist/homebrew-tap`)
- **Installed at**: `/opt/homebrew/bin/perplexity` (via Homebrew)
- **License**: MIT

---

## Directory Structure

```
perplexity-cli/
├── perplexity.py          # Entire CLI — single file, all logic (~420 lines)
├── requirements.txt       # Runtime + test dependencies
├── pytest.ini             # Pytest configuration
├── Makefile               # Standard targets (build/test/test-unit/test-integration/...)
├── README.md
├── llms.txt               # Agent-readable documentation index
├── docs/
│   └── screen.png         # Screenshot used in README
├── tests/
│   ├── conftest.py        # Pytest fixtures (mock_args, mock_api_response, etc.)
│   ├── test_api.py        # Unit tests for Perplexity class + API client
│   ├── test_cli.py        # Integration tests (subprocess-based)
│   ├── test_output.py     # Unit tests for display() formatting
│   └── test_validators.py  # Unit tests for ModelValidator + ApiKeyValidator
└── .github/
    └── workflows/
        └── bump-homebrew-tap.yml  # Auto-bumps formula on GitHub release
```

---

## Code Structure

All logic lives in `perplexity.py` (~420 lines). No submodules, no packages.

### Classes

| Class | Type | Role |
|-------|------|------|
| `ApiKeyNotFoundException` | Exception | Raised when no API key is found |
| `InvalidSelectedModelException` | Exception | Raised when model name is invalid |
| `ApiConfig` | `@dataclass(frozen=True)` | Config container: url, api_key, usage, citations, model |
| `ModelValidator` | Plain class | Static methods: `validate(model)`, `get_AVAILABLE_MODELS()` |
| `ApiKeyValidator` | Plain class | Static method: `get_api_key_from_system()` (reads `$PERPLEXITY_API_KEY`) |
| `Perplexity` | Main class | Initialized with parsed args; handles full request/response lifecycle |

### Key Functions

| Function | Location | Description |
|----------|----------|-------------|
| `get_version()` | module-level | Gets version from `git describe --tags`, falls back to "1.0.0" |
| `display(message, color, bold, bg_color, plaintext)` | module-level | ANSI color printing helper; outputs to stderr |
| `Perplexity.__init__(args)` | class | Validates model + API key, stores config |
| `Perplexity.get_response(message)` | class | POSTs to API, handles response display |
| `Perplexity._show_usage(result, use_glow, plaintext, quiet)` | static | Renders token usage block to stderr |
| `Perplexity._show_citations(result, use_glow, plaintext, quiet)` | static | Renders citations block to stderr |
| `Perplexity._show_content(result)` | instance | Renders answer content to stdout |
| `main()` | module-level | argparse entry point |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (invalid model, missing API key) |
| 2 | Usage error (missing required argument) |
| 3+ | System error (API failure, network issue, missing dependency) |

---

## CLI Interface

**Entry point**: `main()` via `if __name__ == "__main__"` (no setup.py / pyproject.toml — script-only install)

```
perplexity <query> [options]

Positional:
  query                   The question/prompt to send

Options:
  -v, --verbose          Debug logging to stderr
  -u, --usage            Show token usage stats
  -c, --citations        Show source citations
  -g, --glow             Glow-compatible markdown output (# headers instead of ANSI)
  -a, --api-key          API key (default: $PERPLEXITY_API_KEY env var)
  -m, --model            Model name (default: sonar-pro)
  -s, --search-type      pro | fast | auto  (only pro works with sonar-pro)
  -d, --domain-filter    Comma-separated domains to include/exclude (prefix '-' to exclude)
  -r, --recency-filter   day | week | month | year
  -j, --json             Output raw JSON response
  --fields               Comma-separated fields to include in JSON output (with -j)
  --jq                   Pipe JSON output through jq filter (requires jq binary)
  -p, --plaintext        Disable ANSI formatting
  -q, --quiet            Suppress usage and citations output
  --silent               Alias for --quiet
  -o, --output           Write output to file instead of stdout
  --docs                 Print README to stdout and exit
  -V, --version          Print version and exit
```

### Available Models

```python
AVAILABLE_MODELS = sorted([
    "sonar-deep-research",
    "sonar-reasoning-pro",
    "sonar-pro",  # default
    "sonar",
])
```

---

## Dependencies

### Runtime

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | latest | HTTP POST to Perplexity API |

Stdlib: `argparse`, `dataclasses`, `json`, `logging`, `os`, `subprocess`, `sys`

### Testing

| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `pytest-mock` | Mock fixtures |
| `responses` | HTTP mock library |

**Python requirement**: 3.10+ (uses `str | None` union type syntax)

---

## Testing

### Test Organization

| File | Type | Coverage |
|------|------|----------|
| `tests/conftest.py` | Fixtures | `mock_args`, `mock_api_key`, `mock_api_response`, `valid_model`, `invalid_model` |
| `tests/test_api.py` | Unit | Perplexity class init, get_response, web search options, output methods |
| `tests/test_validators.py` | Unit | ModelValidator + ApiKeyValidator |
| `tests/test_output.py` | Unit | display() ANSI formatting |
| `tests/test_cli.py` | Integration | Subprocess tests for all CLI flags, exit codes, help/version/docs |

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make build` | Validate Python syntax (`python3 -m py_compile`) |
| `make test` | Run all tests (`pytest -v`) |
| `make test-unit` | Unit tests only (validators, api, output) |
| `make test-integration` | Integration tests only (CLI subprocess) |
| `make deps` | `pip install -r requirements.txt` |
| `make fmt` | `black perplexity.py tests/` |
| `make lint` | `ruff check perplexity.py tests/` |
| `make check` | `fmt + lint + test` |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, `.coverage`, etc. |
| `make install` | `install -m 755 perplexity.py /usr/local/bin/perplexity` |
| `make dev-install` | Symlink to `/usr/local/bin/` for development |

### Smoke Test (Homebrew)

```ruby
test do
  assert_match "usage:", shell_output("#{bin}/perplexity --help 2>&1")
end
```

---

## Installation

### Via Homebrew (primary distribution method)

```bash
brew tap roboalchemist/tap
brew install perplexity-cli
export PERPLEXITY_API_KEY="your-key"
```

The formula (at `~/github/homebrew-tap/Formula/perplexity-cli.rb`):
1. Copies `perplexity.py` to `libexec/`
2. Pip-installs `requests` into `libexec/vendor/`
3. Creates a bash wrapper at `bin/perplexity` that sets `PYTHONPATH` and calls Python 3.12

### Manual install

```bash
curl -s https://raw.githubusercontent.com/roboalchemist/perplexity-cli/main/perplexity.py > ~/.local/bin/perplexity
chmod +x ~/.local/bin/perplexity
pip install requests
```

### From source

```bash
git clone git@github.com:roboalchemist/perplexity-cli.git
cd perplexity-cli
pip install -r requirements.txt
python perplexity.py "your query"
```

---

## Release Process

1. Create a GitHub release with a version tag (e.g., `v1.1.0`)
2. The `.github/workflows/bump-homebrew-tap.yml` workflow fires automatically:
   - Downloads the release tarball, computes SHA256
   - Clones `roboalchemist/homebrew-tap` using `HOMEBREW_TAP_TOKEN` secret
   - `sed`-patches `url`, `sha256`, and `version` in `Formula/perplexity-cli.rb`
   - Commits and pushes to the tap repo

---

## API Details

- **Endpoint**: `POST https://api.perplexity.ai/chat/completions`
- **Auth**: Bearer token in `Authorization` header
- **System prompt**: `"Be precise and concise."` (hardcoded)
- **Optional `web_search_options`**: `search_type`, `search_domain_filter`, `search_recency_filter`
- **Response path for content**: `choices[0].message.content`
- **Citations**: `result["citations"]` (list of URLs)
- **Usage**: `result["usage"]` (dict of token counts)

---

## Key Files

| File | Purpose |
|------|---------|
| `perplexity.py` | **Everything** — CLI, API client, output formatting |
| `requirements.txt` | Runtime + test dependencies |
| `pytest.ini` | Pytest config (coverage options, testpaths) |
| `Makefile` | Standard build/test targets |
| `llms.txt` | Agent-readable doc index |
| `docs/screen.png` | README screenshot |
| `.github/workflows/bump-homebrew-tap.yml` | Auto-bump Homebrew formula on release |
| `~/github/homebrew-tap/Formula/perplexity-cli.rb` | Homebrew formula (separate repo) |

---

## Relevant Documentation

- `~/github/llm-code-docs/docs/web-scraped/requests/` — requests library docs
- `~/github/llm-code-docs/docs/web-scraped/pytest/en/` — pytest docs
