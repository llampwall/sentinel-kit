"""Prompt rendering utilities."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, Template

from sentinelkit.context.lint import lint_context
from sentinelkit.utils.errors import SentinelKitError, build_error_payload

from . import agents as agent_loader

__all__ = ["PromptRenderer", "PromptRenderingError"]

TEMPLATE_DIR = Path(__file__).with_name("templates")


class PromptRenderingError(SentinelKitError):
    """Raised when prompt rendering fails."""


@dataclass(slots=True)
class CapsuleContext:
    path: str
    content: str
    allowed_context: list[str]


class PromptRenderer:
    """Render router and agent prompts using the Jinja templates."""

    def __init__(
        self,
        *,
        root: Path | str,
        template_dir: Path | str | None = None,
        config_path: Path | str | None = None,
        schema_path: Path | str | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.config_path = Path(config_path) if config_path else None
        self.schema_path = Path(schema_path) if schema_path else None
        directory = Path(template_dir) if template_dir else TEMPLATE_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(directory)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_router_prompt(self, capsule_path: Path | str) -> str:
        capsule = self._build_capsule_context(capsule_path)
        registry = agent_loader.load_agents(root=self.root)
        router_agent = registry.lookup.get("router")
        if router_agent is None:
            raise PromptRenderingError(
                build_error_payload(code="prompts.router_missing", message="Router agent is not defined.")
            )
        template = self._get_template("router.md.j2")
        capsule_data = {
            "path": capsule.path,
            "content": capsule.content,
            "allowed_context": capsule.allowed_context,
        }
        payload = {
            "router": {
                "role": router_agent.role,
                "playbook": router_agent.playbook,
            },
            "capsule": capsule_data,
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "rules_hash": agent.rules_hash,
                    "summary": agent.summary,
                    "routing_keywords": agent.routing_keywords,
                }
                for agent in registry.agents
            ],
        }
        return template.render(**payload).strip() + "\n"

    def render_agent_prompt(self, capsule_path: Path | str, agent_id: str) -> str:
        capsule = self._build_capsule_context(capsule_path)
        registry = agent_loader.load_agents(root=self.root)
        agent = registry.lookup.get(agent_id.lower())
        if agent is None:
            raise PromptRenderingError(
                build_error_payload(
                    code="prompts.agent_missing",
                    message=f"Agent '{agent_id}' does not exist.",
                )
            )
        template = self._get_template("agent.md.j2")
        capsule_data = {
            "path": capsule.path,
            "content": capsule.content,
            "allowed_context": capsule.allowed_context,
        }
        payload = {
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "rules_hash": agent.rules_hash,
                "role": agent.role,
                "playbook": agent.playbook,
                "mount_paths": agent.mount_paths,
            },
            "capsule": capsule_data,
        }
        return template.render(**payload).strip() + "\n"

    def write_router_log(self, capsule_path: Path | str, payload_path: Path | str) -> Path:
        payload = self._read_router_payload(payload_path)
        self._validate_router_payload(payload)
        capsule_abs = self._resolve_path(capsule_path)
        capsule_rel = self._relative_path(capsule_abs)
        log_dir = (self.root / ".sentinel/router_log").resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        slug = capsule_abs.parent.name or capsule_abs.stem
        timestamp = self._timestamp()
        log_path = log_dir / f"{timestamp}-{slug}.jsonl"
        record = {"timestamp": timestamp, "capsule": capsule_rel, "payload": payload}
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record))
            handle.write("\n")
        return log_path

    # Internal helpers -----------------------------------------------------

    def _build_capsule_context(self, capsule_path: Path | str) -> CapsuleContext:
        capsule_abs = self._resolve_path(capsule_path)
        capsule_rel = self._relative_path(capsule_abs)
        self._lint_capsule(capsule_rel)
        text = capsule_abs.read_text(encoding="utf-8")
        allowed = self._extract_allowed_context(text)
        return CapsuleContext(path=capsule_rel, content=text.strip(), allowed_context=allowed)

    def _lint_capsule(self, capsule_rel: str) -> None:
        summary = lint_context(
            root=self.root,
            capsules=[capsule_rel],
            config_path=self.config_path,
            schema_path=self.schema_path,
        )
        errors = [diag for diag in summary.diagnostics if diag.severity == "error"]
        if errors:
            formatted = "\n".join(f"- [{diag.code}] {diag.message}" for diag in errors)
            raise PromptRenderingError(
                build_error_payload(
                    code="prompts.capsule_lint",
                    message=f"Capsule Allowed Context validation failed:\n{formatted}",
                )
            )

    def _get_template(self, name: str) -> Template:
        try:
            return self.env.get_template(name)
        except Exception as error:  # pragma: no cover - template loader errors
            raise PromptRenderingError(
                build_error_payload(code="prompts.template_missing", message=str(error))
            ) from error

    def _resolve_path(self, value: Path | str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (self.root / path).resolve()

    def _relative_path(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def _extract_allowed_context(self, markdown: str) -> list[str]:
        section = self._extract_section(markdown, "Allowed Context")
        if not section:
            return []
        items: list[str] = []
        current = ""
        for raw in section.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("- ") or line.startswith("* ") or line[:2].isdigit():
                if current:
                    items.append(current.strip())
                current = line.split(maxsplit=1)[1] if " " in line else ""
            else:
                current = f"{current} {line}".strip()
        if current:
            items.append(current.strip())
        return items

    def _extract_section(self, markdown: str, heading: str) -> str:
        lines = markdown.splitlines()
        capturing = False
        depth = 0
        bucket: list[str] = []
        for line in lines:
            if line.startswith("#"):
                stripped = line.strip()
                hashes, _, title = stripped.partition(" ")
                if title.lower() == heading.lower():
                    capturing = True
                    depth = len(hashes)
                    continue
                if capturing and len(hashes) <= depth:
                    break
            if capturing:
                bucket.append(line)
        return "\n".join(bucket).strip()

    def _validate_router_payload(self, payload: dict[str, object]) -> None:
        required_strings = ["leadAgent"]
        required_arrays = ["requiredOutputs", "contextToMount"]
        missing = [key for key in required_strings if not isinstance(payload.get(key), str) or not payload[key].strip()]
        missing += [
            key
            for key in required_arrays
            if not isinstance(payload.get(key), Iterable) or not list(payload[key])
        ]
        if missing:
            raise PromptRenderingError(
                build_error_payload(
                    code="prompts.router_payload",
                    message=f"Router payload missing required fields: {', '.join(missing)}",
                )
            )

    def _read_router_payload(self, path: Path | str) -> dict[str, object]:
        payload_path = self._resolve_path(path)
        try:
            return json.loads(payload_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise PromptRenderingError(
                build_error_payload(
                    code="prompts.router_payload_io",
                    message=f"Unable to read router payload '{payload_path}': {error}",
                )
            ) from error
        except json.JSONDecodeError as error:
            raise PromptRenderingError(
                build_error_payload(
                    code="prompts.router_payload_json",
                    message=f"Failed to parse router payload '{payload_path}': {error}",
                )
            ) from error

    def _timestamp(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
