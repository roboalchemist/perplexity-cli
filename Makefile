.PHONY: build clean test test-unit test-integration install dev-install deps fmt lint check help

build:
	# No build step for Python script, just validate
	python3 -m py_compile perplexity.py

clean:
	rm -rf __pycache__ .pytest_cache .coverage dist/ build/ *.egg-info

test:
	pytest -v

test-unit:
	pytest tests/test_validators.py tests/test_api.py tests/test_output.py -v

test-integration:
	pytest tests/test_cli.py -v

install:
	install -m 755 perplexity.py /usr/local/bin/perplexity

dev-install:
	ln -sf $(PWD)/perplexity.py /usr/local/bin/perplexity

deps:
	pip install -r requirements.txt

fmt:
	black perplexity.py tests/

lint:
	ruff check perplexity.py tests/

check: fmt lint test

help:
	@echo "Available targets: build clean test test-unit test-integration install dev-install deps fmt lint check help"
