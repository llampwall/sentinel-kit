SHELL := /usr/bin/env bash
SENTINEL_DIR ?= .sentinel
PNPM_VERSION ?= 9.12.0
PNPM_FLAGS ?=
REPO_URI := $(strip $(shell python - <<'PY'
from pathlib import Path
print(Path('.').resolve().as_uri())
PY
))

.PHONY: sentinel-install

sentinel-install:
	@echo "🔧 Installing specify-cli via uv..."
	uv tool install --from $(REPO_URI) specify-cli
	@echo "📦 Preparing pnpm $(PNPM_VERSION)..."
	corepack enable
	corepack prepare pnpm@$(PNPM_VERSION) --activate
	@echo "📁 Installing $(SENTINEL_DIR) workspace dependencies..."
	cd $(SENTINEL_DIR) && pnpm install $(PNPM_FLAGS)
