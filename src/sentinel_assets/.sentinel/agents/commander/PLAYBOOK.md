# Commander - PLAYBOOK

1) ASSESS
   - Read capsule Goal and Acceptance.
   - Identify required tools (e.g., git, pnpm, node, python, docker, ffmpeg) and minimum versions.

2) DRAFT
   - Create /ops/commander/<capsule>/plan.md with:
     - Goal, prerequisites, env matrix (Windows + WSL/Unix), parameters
     - Dry-run path, execute path, revert path
   - Create /ops/commander/<capsule>/commands.yaml:
     - steps:
       - id: short-name
         when: preflight|dry-run|execute|revert
         bash: "<command>"
         pwsh: "<command>"
         cmd: "<command>"   # only if trivial; otherwise omit
         expect_exit: 0
         timeout_sec: 600
         capture: "logs/<id>.log"

3) PREFLIGHT
   - Add checks for:
     - tool presence and versions (e.g., `node -v`, `ffmpeg -version`)
     - disk space and write permissions
     - path existence for inputs/outputs
   - Include clear failure messages with remediation tips.

4) DRY-RUN
   - Prefer native dry-run flags (e.g., `ffmpeg -nostdin -y -hide_banner -loglevel error -f lavfi -i color=s=1x1:d=0.1 -t 0.1 -f null -`)
   - For git/pnpm/docker, use non-destructive commands or `--dry-run` equivalents.
   - Capture logs to /ops/commander/<capsule>/logs/.

5) EXECUTE
   - Sequence steps with explicit dependencies.
   - Use parameterized paths and safe defaults.
   - For long-running tasks, print periodic progress lines to logs.

6) VERIFY
   - Document explicit checks in /ops/commander/<capsule>/verify.md:
     - file presence/size/hash
     - `--version` outputs
     - command exit codes
   - If results feed other agents, state the handoff files/paths.

7) PACKAGE
   - Ensure plan.md, commands.yaml, verify.md are ASCII-only and within budget.
   - Include Decision-ID and capsule metadata.
   - Summarize how to re-run and how to revert.

8) HANDOFF
   - If repeatable in CI, tag Releaser to convert steps into workflow jobs.
   - If logs/fields should follow Observer schema, tag Observer with an example.
   - If any step implies code edits, tag Builder and stop here.

Notes:
- Provide both PowerShell and bash when possible; note WSL caveats.
- Prefer portable flags and avoid shell-specific features unless documented.
- For ffmpeg or similar tools, include a minimal canonical example users can adapt.
