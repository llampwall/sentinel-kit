# Designer - PLAYBOOK

1) ORIENT
   - Read capsule Goal and Acceptance.
   - Inspect existing tokens, specs, and constraints (brand, platform).

2) DRAFT
   - Propose or extend design tokens (JSON).
   - Write component or flow spec (states, transitions, a11y, keyboard table).
   - Produce copy deck with keys -> strings and tone notes.

3) REVIEW (SELF)
   - Verify contrast ratios and focus order.
   - Provide motion or reduced-motion fallbacks.
   - Confirm each interaction is testable (hook for Verifier).

4) PACKAGE
   - Deliverables:
     - /design/tokens/*.json
     - /design/specs/<feature>/<component>.md
     - /design/copy/<feature>.md
   - Add "Implementation Notes" for Frontender (props, variants, data states).
   - Include Decision and provenance headers.
   - Note: visual outputs should be links or attachments; do not change app code.

5) HANDOFF
   - Router Notes: which components to create or update, risks, open questions.
   - Tag Frontender (implementation) and Verifier (a11y tests).
   - If specialized visual tooling is needed, request a follow-up capsule for a visualdesigner agent.
