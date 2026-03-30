#!/usr/bin/python3
import logging
import argparse
import difflib
import os
import re
import sys
from dataclasses import dataclass
import requests
import json
import subprocess

SKILL_MD = """\
---
name: perplexity-cli
description: CLI for Perplexity AI API with web search, citations, and token usage tracking.
scope: both
---

# Perplexity CLI

## Overview
Single-file Python CLI wrapping the Perplexity AI API. Query web-grounded LLMs from the terminal with formatted output, citations, and search controls.

## Commands

### perplexity (default)
Query Perplexity AI with optional filters and output controls.

### perplexity skill print
Print embedded skill documentation to stdout. Useful for installing the skill.

### perplexity skill add
Install the skill to ~/.claude/skills/perplexity-cli/SKILL.md

## Options
- `-v`, `--verbose`: Enable debug logging
- `-u`, `--usage`: Show token usage statistics
- `-c`, `--citations`: Show source citations
- `-g`, `--glow`: Glow-compatible markdown output (# headers instead of ANSI)
- `-j`, `--json`: Output raw JSON response
- `-a API_KEY`, `--api-key API_KEY`: API key (defaults to PERPLEXITY_API_KEY env var)
- `-m MODEL`, `--model MODEL`: Language model (default: sonar-pro)
- `-s`, `--search-type`: Search type — pro, fast, or auto
- `-d`, `--domain-filter`: Comma-separated domains to include/exclude
- `-r`, `--recency-filter`: Recency filter — day, week, month, or year
- `-p`, `--plaintext`: Output plain text without ANSI formatting
- `-q`, `--quiet`: Suppress usage and citations output
- `-o FILE`, `--output FILE`: Write output to file instead of stdout
- `--docs`: Print README documentation and exit

## Available Models
- sonar-deep-research
- sonar-reasoning-pro
- sonar-pro (default)
- sonar

## Configuration
Set PERPLEXITY_API_KEY environment variable with your API key:
  export PERPLEXITY_API_KEY="your-api-key"

## Examples
  perplexity "What is the meaning of life?"
  perplexity -uc "Explain Einstein's theory"
  perplexity -m sonar-deep-research -r week "latest AI news"
  perplexity -d "github.com,stackoverflow.com" "Python async best practices"
  perplexity -j "who is the president?" | jq .
"""

README_EMBEDDED = """\
# perplexity-cli

## Overview
Perplexity CLI is a command-line client for the Perplexity AI API, allowing users to query web-grounded LLMs directly from the terminal with formatted output, citations, and search controls.

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
- requests library

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
- `-a API_KEY`, `--api-key API_KEY`: API key (defaults to PERPLEXITY_API_KEY env var)
- `-m MODEL`, `--model MODEL`: Language model (default: sonar-pro)
- `-s`, `--search-type`: Search type — `pro`, `fast`, or `auto`
- `-d`, `--domain-filter`: Comma-separated domains to include/exclude (prefix `-` to exclude)
- `-r`, `--recency-filter`: Recency filter — `day`, `week`, `month`, or `year`

## Available Models
- `sonar-deep-research`
- `sonar-reasoning-pro`
- `sonar-pro` (default)
- `sonar`

## License
MIT
"""

AVAILABLE_MODELS = sorted([
    "sonar-deep-research",
    "sonar-reasoning-pro",
    "sonar-pro",
    "sonar"
])

# Determine whether to emit ANSI escape sequences.
# Disable if NO_COLOR is set (https://no-color.org/) or if stderr is not a TTY.
_NO_ANSI = "NO_COLOR" in os.environ or not sys.stderr.isatty()

# Exit codes: 0=success, 1=user error, 2=usage error, 3=system error
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_SYSTEM_ERROR = 3


def get_version() -> str:
    """Get version from git tags, falling back to a default."""
    try:
        # Get git describe output (tag + number of commits since tag)
        proc = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        return proc.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "1.0.0"


VERSION = get_version()

logger = logging.getLogger(__name__)


class ApiKeyNotFoundException(Exception):
    pass


class InvalidSelectedModelException(Exception):
    pass


class SmartParser(argparse.ArgumentParser):
    """ArgumentParser with fuzzy "did you mean?" suggestions for typos."""

    def error(self, message):
        if "unrecognized arguments" in message:
            match = re.search(r"unrecognized arguments: (\S+)", message)
            if match:
                typo = match.group(1)
                flags = []
                for action in self._actions:
                    flags.extend(action.option_strings)
                matches = difflib.get_close_matches(typo, flags, n=1, cutoff=0.6)
                if matches:
                    suggestion = matches[0]
                    sys.stderr.write(f"error: unrecognized arguments: {typo}\n")
                    sys.stderr.write(f"Did you mean: {suggestion}?\n\n")
                    self.print_help(sys.stderr)
                    sys.exit(2)
        super().error(message)


def display(
    message: str,
    color: str = "white",
    bold: bool = False,
    bg_color: str = "black",
    plaintext: bool = False,
):
    colors = {
        "red": "91m",
        "green": "92m",
        "yellow": "93m",
        "blue": "94m",
        "white": "97m",
    }
    bg_colors = {
        "black": "40",
        "red": "41",
        "green": "42",
        "yellow": "43",
        "blue": "44",
        "white": "47",
    }
    if _NO_ANSI or plaintext:
        print(message, file=sys.stderr)
    elif bold:
        print(f"\033[1;{bg_colors[bg_color]};{colors[color]} {message}\033[0m", file=sys.stderr)
    else:
        print(f"\033[{bg_colors[bg_color]};{colors[color]} {message}\033[0m", file=sys.stderr)


@dataclass(frozen=True)
class ApiConfig:
    api_url: str = "https://api.perplexity.ai/chat/completions"
    api_key: str | None = None
    usage: bool = False
    citations: bool = False
    model: str | None = None


class ModelValidator:
    @staticmethod
    def validate(model: str) -> bool:
        return model in AVAILABLE_MODELS

    @staticmethod
    def get_AVAILABLE_MODELS() -> list[str]:
        return AVAILABLE_MODELS


class ApiKeyValidator:
    @staticmethod
    def get_api_key_from_system() -> str | None:
        return os.environ.get("PERPLEXITY_API_KEY")


class Perplexity:
    def __init__(self, args) -> None:
        self.setup = ApiConfig
        if not ModelValidator.validate(args.model):
            raise InvalidSelectedModelException(
                f"Invalid model: {args.model}\n"
                f"Available models: {ModelValidator.get_AVAILABLE_MODELS()}"
            )
        self.setup.model = args.model
        self.setup.usage = args.usage
        self.setup.citations = args.citations
        self.use_glow = args.glow
        self.json_output = args.json
        self.fields = args.fields.split(",") if args.fields else None
        self.jq_filter = args.jq
        self.plaintext = args.plaintext
        self.quiet = args.quiet or args.silent
        self.output_file = args.output
        self.search_type = args.search_type
        self.domain_filter = args.domain_filter
        self.recency_filter = args.recency_filter
        if not args.api_key:
            api_key = ApiKeyValidator.get_api_key_from_system()
            if api_key is None:
                display("Api key not found on system! ", "red")
                logger.debug("Api key not found on system!")
                raise ApiKeyNotFoundException
            else:
                logger.debug(f"Api key found on system: {api_key}")
                self.setup.api_key = api_key
        else:
            self.setup.api_key = args.api_key

    def get_response(self, message) -> None:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.setup.api_key}",
        }
        logger.debug(f"Headers: {headers}")
        query_data = {
            "model": self.setup.model,
            "messages": [
                {"role": "system", "content": "Be precise and concise."},
                {"role": "user", "content": message},
            ],
        }

        web_search_options = {}
        if self.search_type:
            web_search_options["search_type"] = self.search_type
        if self.domain_filter:
            web_search_options["search_domain_filter"] = [
                d.strip() for d in self.domain_filter.split(",")
            ]
        if self.recency_filter:
            web_search_options["search_recency_filter"] = self.recency_filter
        if web_search_options:
            query_data["web_search_options"] = web_search_options

        logger.debug(f"Query data: {query_data}")

        response = requests.post(
            self.setup.api_url, headers=headers, data=json.dumps(query_data)
        )

        if response.status_code == 200:
            result = response.json()
            if self.json_output:
                if self.fields:
                    # Filter result to only include specified fields
                    missing = [f for f in self.fields if f not in result]
                    if missing:
                        print(f"--fields: not found at top level: {', '.join(missing)}", file=sys.stderr)
                    filtered = {k: v for k, v in result.items() if k in self.fields}
                    output = json.dumps(filtered, indent=2)
                else:
                    output = json.dumps(result, indent=2)
                if self.output_file:
                    with open(self.output_file, "w") as f:
                        f.write(output)
                elif self.jq_filter:
                    # Pipe output through jq
                    try:
                        proc = subprocess.run(
                            ["jq", self.jq_filter],
                            input=output,
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        print(proc.stdout)
                    except FileNotFoundError:
                        raise SystemError("jq is not installed. Install from https://stedolan.github.io/jq/")
                    except subprocess.CalledProcessError as e:
                        raise SystemError(f"jq error: {e.stderr}")
                else:
                    print(output)
                return
            if self.setup.citations:
                self._show_citations(result["citations"], self.use_glow, self.plaintext, self.quiet)
            if self.setup.usage:
                self._show_usage(result["usage"], self.use_glow, self.plaintext, self.quiet)
            self._show_content(result["choices"][0]["message"]["content"])
        elif response.status_code == 401:
            display("Invalid api key! ", "red")
        else:
            logger.error(f"Error: {response.status_code}")

    @staticmethod
    def _show_usage(result: dict, use_glow: bool, plaintext: bool = False, quiet: bool = False) -> None:
        if quiet:
            return
        if use_glow:
            print("# Tokens", file=sys.stderr)
        elif plaintext:
            print("Tokens:", file=sys.stderr)
        else:
            display("Tokens \n", "yellow", True, "blue")
        for token in result:
            print(f"- {token}: {result[token]}", file=sys.stderr)
        print("\n", file=sys.stderr)

    @staticmethod
    def _show_citations(result: list, use_glow: bool, plaintext: bool = False, quiet: bool = False) -> None:
        if quiet:
            return
        if use_glow:
            print("# Citations", file=sys.stderr)
        elif plaintext:
            print("Citations:", file=sys.stderr)
        else:
            display("Citations \n", "yellow", True, "blue")
        for element in result:
            print(f"- {element}", file=sys.stderr)
        print("\n", file=sys.stderr)

    def _show_content(self, result: str) -> None:
        if self.use_glow:
            print("# Content", file=sys.stderr)
        elif self.plaintext:
            pass  # No header in plaintext mode
        else:
            display("Content \n", "yellow", True, "blue")
        if self.output_file:
            with open(self.output_file, "w") as f:
                f.write(result)
        else:
            print(result)


EXAMPLES = """\
Examples:
  perplexity "What is the meaning of life?"
  perplexity "Explain Einstein's theory" -c -u
  perplexity "Python async best practices" -d "github.com,stackoverflow.com"
  perplexity "Latest AI news" -r week -c
  perplexity "Who is president?" -j | jq .
  perplexity "Explain quantum computing" -g
"""

def skill_print() -> None:
    """Print the embedded skill documentation to stdout."""
    print(SKILL_MD)


def skill_add() -> None:
    """Install the skill to ~/.claude/skills/perplexity-cli/SKILL.md"""
    skill_dir = os.path.expanduser("~/.claude/skills/perplexity-cli")
    skill_path = os.path.join(skill_dir, "SKILL.md")

    # Create directory if it doesn't exist
    os.makedirs(skill_dir, exist_ok=True)

    # Write the skill file
    with open(skill_path, "w") as f:
        f.write(SKILL_MD)

    display(f"Skill installed to {skill_path}", "green")


def handle_skill_command(args: list[str]) -> bool:
    """Handle skill subcommand. Returns True if handled, False otherwise."""
    if not args or args[0] != "skill":
        return False

    # Check for help flags
    if len(args) > 1 and args[1] in ("-h", "--help"):
        print("usage: perplexity skill [print|add]")
        print("Skill management commands:")
        print("  print    Print skill documentation to stdout")
        print("  add      Install skill to ~/.claude/skills/")
        return True

    if len(args) == 1:
        # Just "skill" - print help
        print("usage: perplexity skill [print|add]")
        print("Skill management commands:")
        print("  print    Print skill documentation to stdout")
        print("  add      Install skill to ~/.claude/skills/")
        return True

    skill_action = args[1]
    if skill_action == "print":
        skill_print()
        return True
    elif skill_action == "add":
        skill_add()
        return True
    else:
        display(f"Unknown skill action: {skill_action}", "red")
        print("usage: perplexity skill [print|add]")
        sys.exit(EXIT_USAGE_ERROR)


def main() -> None:
    # Handle skill subcommand before standard argparse processing
    if handle_skill_command(sys.argv[1:]):
        sys.exit(EXIT_SUCCESS)

    parser = SmartParser(
        epilog=(
            EXAMPLES
            + "\n"
            + "Report bugs to: https://github.com/roboalchemist/perplexity-cli/issues\n"
            + "Homepage: https://github.com/roboalchemist/perplexity-cli"
        ),
    )

    # Add version argument
    parser.add_argument("-V", "--version", action="version",
        version=f"perplexity {VERSION}\nCopyright (C) 2024-2026 Roboalchemist")

    parser.add_argument("query", nargs="?", type=str, help="The query to process (not required with --docs)")

    parser.add_argument("-v", "--verbose", action="store_true", help="Debug mode")
    parser.add_argument("-u", "--usage", action="store_true", help="Show usage")
    parser.add_argument("-c", "--citations", action="store_true", help="Show citations")
    parser.add_argument("-g", "--glow", action="store_true", help="Glow-compatible markdown output (# headers instead of ANSI)")
    parser.add_argument(
        "-a",
        "--api-key",
        type=str,
        help="API key (default: PERPLEXITY_API_KEY env var)",
        required=False,
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="Model name (default: sonar-pro) "
        f"Available models: {AVAILABLE_MODELS}",
        required=False,
        default="sonar-pro",
    )
    parser.add_argument(
        "-s",
        "--search-type",
        type=str,
        choices=["pro", "fast", "auto"],
        help="Web search type (pro|fast|auto). Pro search only works with sonar-pro.",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--domain-filter",
        type=str,
        help="Comma-separated domains to include (or prefix with - to exclude). "
        "Example: 'github.com,stackoverflow.com' or '-reddit.com,-quora.com'",
        required=False,
    )
    parser.add_argument(
        "-r",
        "--recency-filter",
        type=str,
        choices=["day", "week", "month", "year"],
        help="Filter results by recency (day|week|month|year)",
        required=False,
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output raw JSON response instead of formatted text",
    )
    parser.add_argument(
        "--fields",
        type=str,
        help="Comma-separated list of fields to include in JSON output "
        "(e.g., --fields content,citations,usage). Use with --json.",
        required=False,
    )
    parser.add_argument(
        "--jq",
        type=str,
        help="Pipe JSON output through jq with the specified filter. "
        "Requires jq to be installed.",
        required=False,
    )
    parser.add_argument(
        "-p",
        "--plaintext",
        action="store_true",
        help="Output plain text without ANSI formatting",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress usage and citations output",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Suppress usage and citations output (same as --quiet)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Write output to file instead of stdout",
        required=False,
    )
    parser.add_argument(
        "--docs",
        action="store_true",
        help="Print README documentation and exit",
    )
    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.debug(f"args: {args}")

    # Handle --docs flag (no API call needed)
    if args.docs:
        readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
        try:
            with open(readme_path, "r") as f:
                print(f.read())
        except FileNotFoundError:
            display("README.md not found", "red")
            sys.exit(EXIT_SYSTEM_ERROR)
        sys.exit(EXIT_SUCCESS)

    # Validate that query is provided when --docs and skill are not used
    if args.query is None:
        if not sys.stdin.isatty():
            # Read queries from stdin, one per line
            queries = [line.strip() for line in sys.stdin if line.strip()]
            if not queries:
                display("No queries provided via stdin", "red")
                sys.exit(EXIT_USAGE_ERROR)
            for q in queries:
                print(f"\n--- Query: {q} ---\n")
                perplexity = Perplexity(args)
                perplexity.get_response(q)
            return
        display("query is required (use --docs to show documentation, or 'perplexity skill --help')", "red")
        sys.exit(EXIT_USAGE_ERROR)

    try:
        perplexity = Perplexity(args)
        perplexity.get_response(args.query)
    except (InvalidSelectedModelException, ApiKeyNotFoundException) as e:
        # User error - invalid model or missing API key
        if args.json:
            print(json.dumps({
                "error": {
                    "code": EXIT_USER_ERROR,
                    "message": str(e),
                    "type": "user_error"
                }
            }, indent=2), file=sys.stderr)
        logger.debug(f"User error: {str(e)}")
        sys.exit(EXIT_USER_ERROR)
    except Exception as e:
        # System error - API failure, network issue, etc.
        if args.json:
            print(json.dumps({
                "error": {
                    "code": EXIT_SYSTEM_ERROR,
                    "message": str(e),
                    "type": "system_error"
                }
            }, indent=2), file=sys.stderr)
        logger.debug(f"System error: {str(e)}")
        sys.exit(EXIT_SYSTEM_ERROR)


if __name__ == "__main__":
    main()
