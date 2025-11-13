"""Capsule generator implementation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sentinelkit.context.allowed_context import build_allowed_context
from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = [
    "CapsuleGenerator",
    "CapsuleGeneratorError",
    "CapsuleResult",
]

MAX_LINES = 300
TEMPLATE_PATH = Path(".sentinel/templates/capsule.md")


@dataclass(slots=True)
class CapsuleInputs:
    spec: str
    plan: str
    tasks: str
    goal: str
    required_outputs: list[str]
    acceptance_criteria: list[str]
    router_notes: list[str]
    context_seeds: list[str]


class CapsuleGeneratorError(SentinelKitError):
    """Raised when capsule generation fails."""


class CapsuleGenerator:
    """Generate deterministic capsules from Spec-Kit feature folders."""

    def __init__(self, *, root: Path | str) -> None:
        self.root = Path(root).resolve()

    def generate(
        self,
        spec_dir: Path | str,
        decision: str,
        *,
        agent: str = "ROUTER",
        rules_hash: str | None = None,
        write: bool = True,
    ) -> CapsuleResult:
        spec_path = self._validate_spec_dir(spec_dir)
        inputs = self._load_inputs(spec_path)
        capsule_id = self._hash_capsule(spec_path.name, inputs)
        header = self._build_header(agent=agent, rules_hash=rules_hash or f"{agent}@1.0", decision=decision)
        allowed_context = self._build_allowed_context(spec_path, inputs.context_seeds)
        template = self._load_template()
        content = self._render(
            template=template,
            header=header,
            capsule_id=capsule_id,
            inputs=inputs,
            allowed_context=allowed_context,
        )
        self._enforce_line_budget(content)
        out_path = spec_path / "capsule.md"
        if write:
            out_path.write_text(content, encoding="utf-8", newline="\n")
        return CapsuleResult(path=out_path, content=content)

    def _validate_spec_dir(self, spec_dir: Path | str) -> Path:
        path = Path(spec_dir)
        resolved = path if path.is_absolute() else (self.root / path)
        resolved = resolved.resolve()
        if not resolved.is_dir():
            raise CapsuleGeneratorError(
                build_error_payload(
                    code="capsule.invalid_spec_dir",
                    message=f"Spec directory '{resolved}' does not exist.",
                )
            )
        required = ["spec.md", "plan.md", "tasks.md"]
        missing = [file for file in required if not (resolved / file).exists()]
        if missing:
            raise CapsuleGeneratorError(
                build_error_payload(
                    code="capsule.missing_files",
                    message=f"Spec directory missing required files: {', '.join(missing)}",
                )
            )
        return resolved

    def _load_inputs(self, spec_dir: Path) -> CapsuleInputs:
        spec = (spec_dir / "spec.md").read_text(encoding="utf-8")
        plan = (spec_dir / "plan.md").read_text(encoding="utf-8")
        tasks = (spec_dir / "tasks.md").read_text(encoding="utf-8")

        goal = self._extract_section(spec, "Goal")
        required_outputs = self._extract_list(tasks, "Required Outputs")
        acceptance_criteria = self._extract_list(tasks, "Acceptance Criteria")
        router_notes = self._extract_list(plan, "Router Notes")
        context_seeds = self._extract_list(plan, "Allowed Context Seeds")

        if not goal:
            raise CapsuleGeneratorError(
                build_error_payload(code="capsule.missing_goal", message="spec.md must define a 'Goal' section.")
            )
        for name, items in (
            ("Required Outputs", required_outputs),
            ("Acceptance Criteria", acceptance_criteria),
            ("Router Notes", router_notes),
        ):
            if not items:
                raise CapsuleGeneratorError(
                    build_error_payload(
                        code="capsule.missing_section",
                        message=f"'{name}' must contain at least one bullet in tasks/plan.",
                    )
                )
        return CapsuleInputs(
            spec=spec,
            plan=plan,
            tasks=tasks,
            goal=self._normalize_paragraph(goal),
            required_outputs=required_outputs,
            acceptance_criteria=acceptance_criteria,
            router_notes=router_notes,
            context_seeds=context_seeds,
        )

    def _hash_capsule(self, slug: str, inputs: CapsuleInputs) -> str:
        digest = hashlib.sha256(f"{inputs.spec}{inputs.plan}{inputs.tasks}".encode("utf-8")).hexdigest()[:8]
        return f"{slug}@{digest}"

    def _build_header(self, *, agent: str, rules_hash: str, decision: str) -> str:
        return "\n".join(
            [
                "<!--",
                f"  ProducedBy={agent}",
                f"  RulesHash={rules_hash}",
                f"  Decision={decision}",
                "-->",
            ]
        )

    def _build_allowed_context(self, spec_dir: Path, seeds: list[str]) -> list[str]:
        defaults = [
            str((spec_dir / "spec.md").relative_to(self.root)),
            str((spec_dir / "plan.md").relative_to(self.root)),
            str((spec_dir / "tasks.md").relative_to(self.root)),
        ]
        normalized_seeds = [
            seed.strip()
            for seed in seeds
            if seed.strip() and not seed.strip().startswith("#")
        ]
        return build_allowed_context(root=self.root, seeds=[*defaults, *normalized_seeds])

    def _load_template(self) -> str:
        template_path = (self.root / TEMPLATE_PATH).resolve()
        if not template_path.exists():
            raise CapsuleGeneratorError(
                build_error_payload(
                    code="capsule.missing_template",
                    message=f"Capsule template '{template_path}' does not exist.",
                )
            )
        return template_path.read_text(encoding="utf-8")

    def _render(
        self,
        *,
        template: str,
        header: str,
        capsule_id: str,
        inputs: CapsuleInputs,
        allowed_context: list[str],
    ) -> str:
        replacements = {
            "{{PRODUCED_BY}}": header,
            "{{CAPSULE_ID}}": capsule_id,
            "{{GOAL}}": inputs.goal,
            "{{REQUIRED_OUTPUTS}}": self._format_list(inputs.required_outputs),
            "{{ACCEPTANCE_CRITERIA}}": self._format_list(inputs.acceptance_criteria),
            "{{ALLOWED_CONTEXT}}": self._format_list(allowed_context),
            "{{ROUTER_NOTES}}": self._format_list(inputs.router_notes),
        }
        content = template
        for token, value in replacements.items():
            content = content.replace(token, value)
        return content.strip() + "\n"

    def _enforce_line_budget(self, content: str) -> None:
        line_count = content.count("\n") + 1
        if line_count > MAX_LINES:
            raise CapsuleGeneratorError(
                build_error_payload(
                    code="capsule.line_budget",
                    message=f"Capsule exceeds {MAX_LINES} lines (rendered {line_count}).",
                )
            )

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

    def _extract_list(self, markdown: str, heading: str) -> list[str]:
        section = self._extract_section(markdown, heading)
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

    def _normalize_paragraph(self, section: str) -> str:
        return "\n".join(line.strip() for line in section.splitlines() if line.strip())

    def _format_list(self, items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items)


__all__ = ["CapsuleGenerator", "CapsuleGeneratorError"]
@dataclass(slots=True)
class CapsuleResult:
    path: Path
    content: str
