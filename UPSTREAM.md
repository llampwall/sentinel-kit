# Upstream Sync Strategy

SentinelKit is a downstream fork of [GitHub Spec Kit](https://github.com/github/spec-kit). This document tracks how we stay aligned with upstream while layering on the Sentinel-specific enforcement tooling.

## Source of Truth

- **Upstream repo:** `github/spec-kit`
- **Current base commit:** _TBD (record commit SHA after each sync)_
- **Downstream repo:** `llampwall/sentinel-kit`

## Sync Cadence

- Perform an upstream pull at the start of each significant SentinelKit milestone (roughly every 1–2 weeks).
- Open a dedicated `sync/<YYYY-MM-DD>` branch that merges upstream `main` into downstream `main`.
- Resolve conflicts locally; when Sentinel-specific files diverge, prefer the Sentinel version but annotate the reasoning in the PR description.
- Tag each successful sync with `sync-<YYYYMMDD>` once merged.

## Manual Sync Steps

1. Ensure your local `main` is clean and up to date:
   ```bash
   git checkout main
   git fetch origin
   git pull origin main
   ```
2. Fetch upstream and create the sync branch:
   ```bash
   git remote add upstream https://github.com/github/spec-kit.git   # only once
   git fetch upstream
   git checkout -b sync/2025-11-08 upstream/main
   ```
3. Merge downstream changes:
   ```bash
   git merge origin/main
   ```
4. Resolve conflicts, run the full bootstrap (see README “Install Sentinel tooling”), and verify:
   ```bash
   make sentinel-install
   (cd .sentinel && pnpm lint && pnpm typecheck && pnpm test)
   ```
5. Push the sync branch and open a PR summarizing conflicts, notable upstream updates, and affected Sentinel modules.
6. After merge, update this document with the new base commit SHA.

## Sentinel-Specific Surfaces

The following directories/files are owned by SentinelKit and should not be overwritten by upstream syncs without deliberate review:

- `.sentinel/**`
- `.taskmaster/**`
- `.specify/**` (once capsules/agents are added)
- `UPSTREAM.md`, `README.md` additions, `Makefile`, `scripts/setup.ps1`

If upstream introduces conflicting changes, prefer our downstream implementation and file an issue to reconcile behavior later.

## Verification Checklist After Sync

- [ ] `specify --version` reports the same value in both repositories.
- [ ] `node .sentinel/scripts/orch/prompt-render.mjs --help` works with upstream capsule format.
- [ ] `pnpm install && pnpm lint && pnpm typecheck && pnpm vitest` succeed inside `.sentinel/`.
- [ ] Task Master tasks remain valid (`task-master validate-dependencies`).
- [ ] CI scripts (once added) pass against the merged branch.
