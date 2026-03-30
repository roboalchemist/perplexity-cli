## Perplexity CLI 🔎
![screen](docs/screen.png)
Perplexity CLI is a simple command-line client for the Perplexity AI API, allowing users to query web-grounded LLMs directly from the terminal with formatted output, citations, and search controls.

## Features
- Easy querying of the Perplexity API with web-grounded answers
- Support for multiple language models (sonar-pro, sonar-deep-research, etc.)
- Optional display of token usage statistics
- Optional display of source citations
- Colorful output formatting (with glow support)
- Search controls: recency filter, domain filter, search type
- Raw JSON output mode
- API key from environment variable or command-line argument

## Requirements
- Python 3.10+
- `requests` library

## Installation

### Via Homebrew (recommended)
```bash
brew tap roboalchemist/tap
brew install perplexity-cli
export PERPLEXITY_API_KEY="your-api-key"
```

### Manual
```bash
curl -s https://raw.githubusercontent.com/roboalchemist/perplexity-cli/main/perplexity.py > ~/.local/bin/perplexity
chmod +x ~/.local/bin/perplexity
pip install requests
export PERPLEXITY_API_KEY="your-api-key"
```

### From source
```bash
git clone https://github.com/roboalchemist/perplexity-cli.git
cd perplexity-cli
pip install requests
python perplexity.py "your query"
```

## Usage
```bash
perplexity "What is the meaning of life?"
```

```bash
# Show citations and token usage
perplexity -uc "Explain Einstein's theory of relativity"

# Use deep research model with recent results
perplexity -m sonar-deep-research -r week "latest AI research breakthroughs"

# Filter to specific domains
perplexity -d "arxiv.org,nature.com" "quantum computing advances"

# Exclude domains
perplexity -d "-reddit.com" "Python async best practices"

# Raw JSON output
perplexity -j "who is the president?" | jq .
```

## Options
- `-v`, `--verbose`: Enable debug logging
- `-u`, `--usage`: Show token usage statistics
- `-c`, `--citations`: Show source citations
- `-g`, `--glow`: Use Glow-compatible markdown formatting (# headers instead of ANSI)
- `-j`, `--json`: Output raw JSON response
- `-a API_KEY`, `--api-key API_KEY`: API key (defaults to `PERPLEXITY_API_KEY` env var)
- `-m MODEL`, `--model MODEL`: Language model (default: sonar-pro)
- `-s`, `--search-type`: Search type — `pro`, `fast`, or `auto`
- `-d`, `--domain-filter`: Comma-separated domains to include/exclude (prefix `-` to exclude)
- `-r`, `--recency-filter`: Recency filter — `day`, `week`, `month`, or `year`

## Available Models
- `sonar-deep-research`
- `sonar-reasoning-pro`
- `sonar-pro` (default)
- `sonar`

## Configuration
Set the `PERPLEXITY_API_KEY` environment variable with your Perplexity API key:
```bash
export PERPLEXITY_API_KEY="your-api-key"
```

For full configuration reference, see [docs/config.md](docs/config.md).

## License
MIT
