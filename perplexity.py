#!/usr/bin/python3
import logging
import argparse
import os
import sys
from dataclasses import dataclass
import requests
import json

AVAILABLE_MODELS = [
    "sonar-deep-research",
    "sonar-reasoning-pro",
    "sonar-pro",
    "sonar"
]

# Determine whether to emit ANSI escape sequences.
# Disable if NO_COLOR is set (https://no-color.org/) or if stderr is not a TTY.
_NO_ANSI = "NO_COLOR" in os.environ or not sys.stderr.isatty()

# Exit codes: 0=success, 1=user error, 2=usage error, 3=system error
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_SYSTEM_ERROR = 3

logger = logging.getLogger(__name__)


class ApiKeyNotFoundException(Exception):
    pass


class InvalidSelectedModelException(Exception):
    pass


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
        self.plaintext = args.plaintext
        self.quiet = args.quiet or args.silent
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
                print(json.dumps(result, indent=2))
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
        print(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="The query to process")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug mode")
    parser.add_argument("-u", "--usage", action="store_true", help="Show usage")
    parser.add_argument("-c", "--citations", action="store_true", help="Show citations")
    parser.add_argument("-g", "--glow", action="store_true", help="Show citations")
    parser.add_argument(
        "-a",
        "--api-key",
        type=str,
        help="Description for api_key argument",
        required=False,
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="Description for model argument (default: sonar-pro) "
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
    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.debug(f"args: {args}")
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
