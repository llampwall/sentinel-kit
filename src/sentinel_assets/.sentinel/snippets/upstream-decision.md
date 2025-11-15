## Decision Ledger & Provenance

- Keep `.sentinel/DECISIONS.md` in sync whenever you pull from upstream or land a sync branch. After conflicts are resolved, run the decision-log CLI to capture the sync rationale and reference the touched files.
- Suggested command (tweak scope/summary/outputs for the specific sync):

```bash
cd .sentinel
node scripts/decision-log.mjs \
  --author Maintainer \
  --scope "sync/<YYYY-MM-DD>" \
  --summary "Merge spec-kit upstream into sentinel-kit" \
  --rationale "Rebase onto upstream main" \
  --outputs "UPSTREAM.md,.sentinel/**"
```

- Copy the emitted `ProducedBy=` snippet (choose the language-appropriate form) into every file you touched during the sync, especially `.sentinel/DECISIONS.md` and `UPSTREAM.md`.
- When the ledger grows beyond ~300 lines, archive older entries into `DECISIONS.archive.md` before continuing; this keeps provenance audits lightweight.
