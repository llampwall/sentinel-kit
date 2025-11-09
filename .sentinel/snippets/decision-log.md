## Decision & Provenance Workflow

Record every architectural or workflow change in `.sentinel/DECISIONS.md` using the decision-log CLI so provenance stays aligned with the code.

1. Run the CLI from the `.sentinel/` workspace after you finish a change:

   ```bash
   cd .sentinel
   node scripts/decision-log.mjs \
     --author Builder \
     --scope ".sentinel/scripts/orch" \
     --summary "Adopt Eta prompt renderer" \
     --rationale "Unified templates + logging" \
     --outputs ".sentinel/scripts/orch/prompt-render.mjs,README.md"
   ```

   Required flags: `--author`, `--scope`, `--summary` (alias `--decision`), `--rationale`, and at least one `--outputs` entry (comma-separated list). Optional flags include `--supersedes`, `--agent`, `--rulesHash`, `--date`, and `--ledger`.

2. The CLI acquires a lock, bumps `NEXT_ID`, appends the entry, and prints JSON containing language-specific `ProducedBy=…` snippets (plain, JS/TS, Python/Shell, Markdown). Copy the snippet that matches each file type and paste it at the top of every file you touched.

3. Keep the ledger lightweight: when it grows beyond ~300 lines, archive older entries into `DECISIONS.archive.md` before adding more entries.

Following this workflow ensures every artifact references the decision that introduced it.
