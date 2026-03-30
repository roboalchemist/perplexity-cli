# Configuration

## Environment Variables

| Variable | Required | Default | Description |
|---------|----------|---------|-------------|
| `PERPLEXITY_API_KEY` | Yes | — | API key for api.perplexity.ai |
| `NO_COLOR` | No | — | If set, disables all ANSI output |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (invalid model, missing API key) |
| 2 | Usage error (missing required argument) |
| 3 | System error (network failure, jq not found) |

## Output Modes

- `--json` — raw API JSON to stdout
- `--plaintext` / `-p` — no ANSI formatting
- `--glow` — markdown-compatible (# headers instead of ANSI)
- `--quiet` / `--silent` — suppress usage/citations stderr output
