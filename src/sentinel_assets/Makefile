SHELL := /usr/bin/env bash
PYTHON ?= python

.PHONY: bootstrap sync selfcheck test lint

bootstrap:
	$(PYTHON) scripts/bootstrap.py

sync:
	uv sync

selfcheck:
	uv run sentinel selfcheck

test:
	uv run pytest -q

lint:
	uv run ruff check
