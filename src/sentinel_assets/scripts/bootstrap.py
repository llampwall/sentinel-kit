"""SentinelKit bootstrap runner for Python-only workflow."""

from __future__ import annotations

import subprocess
from typing import Sequence

COMMANDS: Sequence[Sequence[str]] = (
    ("uv", "sync"),
    ("uv", "run", "sentinel", "selfcheck"),
    ("uv", "run", "pytest", "-q"),
)


def run_command(command: Sequence[str]) -> None:
    """Execute *command* and stream output."""
    print(f"$ {' '.join(command)}")
    subprocess.check_call(command)


def main() -> None:
    """Run the standard SentinelKit bootstrap sequence."""
    for command in COMMANDS:
        run_command(command)


if __name__ == "__main__":
    main()
