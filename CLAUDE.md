# perplexity-cli — CLAUDE.md

## Project Overview

A single-file Python CLI tool that wraps the [Perplexity AI API](https://docs.perplexity.ai/) (`api.perplexity.ai/chat/completions`). Users query Perplexity's web-grounded LLMs from the terminal and get formatted responses with optional citations, token usage stats, and search controls.

- **Public repo**: `~/github/perplexity-cli` → `github.com/roboalchemist/perplexity-cli`
- **Homebrew tap**: `roboalchemist/tap/perplexity-cli` (public tap at `github.com/roboalchemist/homebrew-tap`)
- **Installed at**: `/opt/homebrew/bin/perplexity` (v1.0.0, Python 3.12)
- **License**: MIT

---

## Directory Structure

```
perplexity-cli/
├── perplexity.py          # Entire CLI — single file, all logic here
├── requirements.txt       # requests (only dependency)
├── README.md
├── .gitignore             # Standard Python gitignore
├── docs/
│   └── screen.png         # Screenshot used in README
└── .github/
    └── workflows/
        └── bump-homebrew-tap.yml  # Auto-bumps formula on GitHub release
```

---

## Code Structure (AST)

All logic lives in `perplexity.py` (~255 lines). No submodules, no packages.

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
| `display(message, color, bold, bg_color)` | module-level | ANSI color printing helper |
| `Perplexity.__init__(args)` | class | Validates model + API key, stores config |
| `Perplexity.get_response(message)` | class | POSTs to API, handles response display |
| `Perplexity._show_usage(result, use_glow)` | static | Renders token usage block |
| `Perplexity._show_citations(result, use_glow)` | static | Renders citations block |
| `Perplexity._show_content(result)` | instance | Renders answer content |
| `main()` | module-level | argparse entry point |

---

## CLI Interface

**Entry point**: `main()` via `if __name__ == "__main__"` (no setup.py / pyproject.toml — script-only install)

```
perplexity <query> [options]

Positional:
  query                   The question/prompt to send

Options:
  -v, --verbose           Debug logging
  -u, --usage             Show token usage stats
  -c, --citations         Show source citations
  -g, --glow              Glow-compatible markdown output (# headers instead of ANSI)
  -a, --api-key           API key (default: $PERPLEXITY_API_KEY env var)
  -m, --model             Model name (default: sonar-pro)
  -s, --search-type       pro | fast | auto  (only pro works with sonar-pro)
  -d, --domain-filter     Comma-separated domains to include/exclude (prefix '-' to exclude)
  -r, --recency-filter    day | week | month | year
  -j, --json              Output raw JSON response
```

### Available Models (as of Feb 2026)

```python
AVAILABLE_MODELS = [
    "sonar-deep-research",
    "sonar-reasoning-pro",
    "sonar-pro",      # default
    "sonar",
]
```

> **Note**: The installed Homebrew version (v1.0.0) is stale — it still shows old `llama-3.1-sonar-*` model names. The repo `perplexity.py` is current.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | latest | HTTP POST to Perplexity API |
| `argparse` | stdlib | CLI argument parsing |
| `dataclasses` | stdlib | `ApiConfig` data container |
| `json` | stdlib | Serialize request body, pretty-print raw response |
| `logging` | stdlib | Debug output via `-v` |
| `os` | stdlib | Read `PERPLEXITY_API_KEY` env var |

**Python requirement**: 3.10+ (uses `str | None` union type syntax)

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
pip install requests
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

The `/brew-bump` skill can also do this manually.

---

## Testing

No test suite. The Homebrew formula has a smoke test:
```ruby
test do
  assert_match "usage:", shell_output("#{bin}/perplexity --help 2>&1")
end
```

**Manual smoke test**:
```bash
perplexity "hello" -m sonar
perplexity "who wrote hamlet" -c -u -m sonar-pro
perplexity "latest news" -r day -j | jq .
```

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
| `requirements.txt` | `requests` only |
| `.github/workflows/bump-homebrew-tap.yml` | Auto-bump Homebrew formula on release |
| `~/github/homebrew-tap/Formula/perplexity-cli.rb` | Homebrew formula (separate repo) |
