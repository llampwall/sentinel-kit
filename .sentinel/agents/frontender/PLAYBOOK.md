# Frontender - PLAYBOOK

1) ORIENT
   - Read capsule Goal and Acceptance.
   - Open Designer spec, tokens, and copy deck for the feature.

2) PLAN
   - List components/pages to create or update and their states (loading/empty/error/success).
   - Define props and variants; note any data needed from API/clients.
   - Create a minimal checklist for a11y (focus order, roles, keyboard, labels).

3) IMPLEMENT
   - Add or update UI files under /web/src/** using the repo’s stack.
   - Apply tokens; add ARIA attributes and keyboard handlers.
   - Create a story and a simple fixture set for primary states where helpful.

4) VERIFY
   - Run `pnpm lint`, `pnpm typecheck`, and `pnpm build`.
   - Quick manual check with keyboard only; verify focus traps and esc behavior where relevant.
   - If tests exist, ensure they pass; if gaps exist, note them for Verifier.

5) PACKAGE
   - Write “Implementation Notes” for the capsule:
     - props, variants, state machine notes, keyboard interactions, known limitations.
   - Include provenance headers in the PR description or notes.

6) HANDOFF
   - If data gaps exist: open a note for Integrator specifying exact fields and endpoints needed.
   - Tag Verifier to add or update tests, including a11y assertions if not covered.
   - If any deviation from Designer tokens/specs occurred, document why and propose a follow-up.
