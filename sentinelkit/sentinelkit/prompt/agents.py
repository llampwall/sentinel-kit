"""Agent registry utilities."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = ["AgentRegistry", "load_agents"]


class AgentRegistryError(SentinelKitError):
    """Raised when agent loading fails."""


@dataclass(slots=True)
class AgentMetadata:
    id: str
    name: str
    rules_hash: str
    summary: str
    routing_keywords: list[str]
    mount_paths: list[str]
    role: str
    playbook: str


@dataclass(slots=True)
class AgentRegistry:
    agents: list[AgentMetadata]
    lookup: dict[str, AgentMetadata]


def load_agents(*, root: Path | str) -> AgentRegistry:
    root_path = Path(root).resolve()
    agents_dir = root_path / ".sentinel/agents"
    if not agents_dir.exists():
        raise AgentRegistryError(
            build_error_payload(
                code="agents.missing_dir",
                message=f"Agent directory '{agents_dir}' does not exist.",
            )
        )

    agents: list[AgentMetadata] = []
    errors: list[str] = []
    for entry in sorted(agents_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            agents.append(_load_agent(entry, root_path))
        except AgentRegistryError as error:
            errors.append(f"[{entry.name}] {error.payload.message}")

    if errors:
        raise AgentRegistryError(
            build_error_payload(code="agents.load_failed", message="; ".join(errors))
        )

    lookup = {agent.id.lower(): agent for agent in agents}
    return AgentRegistry(agents=agents, lookup=lookup)


def _load_agent(agent_dir: Path, root: Path) -> AgentMetadata:
    config_path = agent_dir / "agent.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise AgentRegistryError(
            build_error_payload(
                code="agents.read_json",
                message=f"Unable to read '{config_path}': {error}",
            )
        ) from error
    except json.JSONDecodeError as error:
        raise AgentRegistryError(
            build_error_payload(
                code="agents.parse_json",
                message=f"Failed to parse '{config_path}': {error}",
            )
        ) from error

    required_strings = ["id", "name", "rulesHash", "summary"]
    missing = [field for field in required_strings if not _is_non_empty_string(config.get(field))]
    if missing:
        raise AgentRegistryError(
            build_error_payload(
                code="agents.missing_fields",
                message=f"agent.json missing fields: {', '.join(missing)}",
            )
        )

    mount_paths = config.get("mount_paths") or []
    prompt_files = config.get("prompt_files") or []
    if not isinstance(mount_paths, list) or not all(_is_non_empty_string(item) for item in mount_paths):
        raise AgentRegistryError(
            build_error_payload(code="agents.mounts_invalid", message="mount_paths must be an array of strings.")
        )
    if not isinstance(prompt_files, list) or not all(_is_non_empty_string(item) for item in prompt_files):
        raise AgentRegistryError(
            build_error_payload(code="agents.prompts_invalid", message="prompt_files must be an array of strings.")
        )

    prompts = [_read_prompt(root / path) for path in prompt_files]
    role = _find_prompt(prompts, "ROLE.md")
    playbook = _find_prompt(prompts, "PLAYBOOK.md")
    if role is None or playbook is None:
        raise AgentRegistryError(
            build_error_payload(
                code="agents.prompt_missing",
                message="ROLE.md and PLAYBOOK.md must be listed in prompt_files.",
            )
        )

    routing_keywords = config.get("routing_keywords") or []
    if not isinstance(routing_keywords, list):
        routing_keywords = []

    return AgentMetadata(
        id=config["id"],
        name=config["name"],
        rules_hash=config["rulesHash"],
        summary=config["summary"],
        routing_keywords=[kw for kw in routing_keywords if _is_non_empty_string(kw)],
        mount_paths=[_normalize_path(path) for path in mount_paths],
        role=role,
        playbook=playbook,
    )


def _read_prompt(path: Path) -> tuple[str, str]:
    try:
        return (path.name, path.read_text(encoding="utf-8").strip())
    except OSError as error:
        raise AgentRegistryError(
            build_error_payload(
                code="agents.prompt_io",
                message=f"Unable to read prompt '{path}': {error}",
            )
        ) from error


def _find_prompt(prompts: list[tuple[str, str]], needle: str) -> str | None:
    needle_lower = needle.lower()
    for name, content in prompts:
        if name.lower().endswith(needle_lower):
            return content
    return None


def _normalize_path(path: str) -> str:
    return Path(path).as_posix()


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""
