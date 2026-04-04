from __future__ import annotations

from pathlib import Path

from backend.mcp.models import McpRegistryFile


def load_registry(path: Path) -> McpRegistryFile:
    text = path.read_text(encoding="utf-8")
    return McpRegistryFile.model_validate_json(text)


def resolve_cwd(cwd: str | None, monorepo_root: Path) -> str | None:
    if cwd is None:
        return None
    p = Path(cwd)
    if not p.is_absolute():
        p = monorepo_root / p
    return str(p.resolve())
