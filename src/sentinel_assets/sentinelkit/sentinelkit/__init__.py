"""SentinelKit public package surface."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from typing import Final, Tuple

__all__ = [
    "__version__",
    "VersionInfo",
    "get_version",
    "get_version_info",
    "version_components",
]


@dataclass(frozen=True)
class VersionInfo:
    """Structured view of the package version."""

    raw: str
    base: str
    prerelease: str | None = None
    local: str | None = None

    def as_tuple(self) -> Tuple[str, ...]:
        """Return the dotted base version as a tuple of strings."""
        return tuple(self.base.split("."))


def _resolve_version() -> str:
    try:
        return importlib_metadata.version("sentinelkit")
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover - fallback for editable installs
        return "0.0.0a0"


def _build_version_info(raw: str) -> VersionInfo:
    base_plus, *local = raw.split("+", 1)
    base, *pre = base_plus.split("-", 1)
    return VersionInfo(
        raw=raw,
        base=base,
        prerelease=pre[0] if pre else None,
        local=local[0] if local else None,
    )


__version__: Final[str] = _resolve_version()
_VERSION_INFO: Final[VersionInfo] = _build_version_info(__version__)


def get_version() -> str:
    """Return the semantic version string for this installation."""
    return __version__


def get_version_info() -> VersionInfo:
    """Return the structured version metadata."""
    return _VERSION_INFO


def version_components() -> Tuple[str, ...]:
    """Convenience helper that exposes the version's dotted components."""
    return _VERSION_INFO.as_tuple()
