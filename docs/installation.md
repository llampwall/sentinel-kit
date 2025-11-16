# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), [Codebuddy CLI](https://www.codebuddy.ai/cli) or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation

### Install the Specify CLI (once per machine)

```bash
uv tool install specify-cli --from git+https://github.com/llampwall/sentinel-kit.git
```

This publishes a global `specify` command that includes SentinelKit's project scaffolding.

### Initialize a new project

```bash
specify init <PROJECT_NAME> --sentinel
```

Already inside the folder you want to scaffold? Run `specify init . --sentinel` or `specify init --here --sentinel`.

### Specify AI assistant

You can proactively select your AI assistant when calling `specify init` (otherwise you'll be prompted):

```bash
specify init <project_name> --sentinel --ai claude
specify init <project_name> --sentinel --ai gemini
specify init <project_name> --sentinel --ai copilot
specify init <project_name> --sentinel --ai codebuddy
```

### Specify script type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:

- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:

```bash
specify init <project_name> --sentinel --script sh
specify init <project_name> --sentinel --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
specify init <project_name> --sentinel --ai claude --ignore-agent-tools
```

### Ephemeral one-off usage

Prefer to avoid installing the CLI globally? Run:

```bash
uvx --from git+https://github.com/llampwall/sentinel-kit.git specify init <PROJECT_NAME> --sentinel
```

After the scaffold completes, continue inside the project directory with `uv sync`, `uv run sentinel ...`, and `specify check` as usual.

### Verify the Sentinel gate

Run the core workflow once inside the new repo:

```bash
uv sync
uv run sentinel selfcheck
specify check
```

- Use `uv run sentinel --format json selfcheck` when you need machine-readable output.
- Expect early runs to flag `capsule`, `context`, `contracts`, `mcp`, and `sentinels` as **pending** until you wire up MCP configs and sentinel pytest suites. Pending checks keep the exit code at 0 so you can land scaffolding before the enforcement assets are ready.

## Verification

After initialization, you should see the following commands available in your AI agent:

- `/speckit.specify` - Create specifications
- `/speckit.plan` - Generate implementation plans  
- `/speckit.tasks` - Break down into actionable tasks

The `.specify/scripts` directory will contain both `.sh` and `.ps1` scripts.

## Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
