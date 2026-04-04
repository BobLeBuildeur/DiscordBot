from __future__ import annotations

import asyncio
import json
import logging

from mcp import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    get_default_environment,
    stdio_client,
)

from backend.config import Settings
from backend.mcp.registry import load_registry, resolve_cwd
from backend.mcp.runtime import McpRegistryRuntime
from backend.orchestrator.models import SessionState, TurnRecord, TurnRole
from backend.orchestrator.store import FileBackedSessionStore

logger = logging.getLogger(__name__)


def _tool_text(result: object) -> str:
    chunks: list[str] = []
    for block in result.content:
        if getattr(block, "type", None) == "text" and hasattr(block, "text"):
            chunks.append(block.text)
    return "".join(chunks)


class KnowledgeEnrichmentService:
    """Calls the books MCP (find_books + get_book) and persists silent knowledge turns."""

    def __init__(
        self,
        settings: Settings,
        store: FileBackedSessionStore,
        runtime: McpRegistryRuntime,
    ) -> None:
        self._settings = settings
        self._store = store
        self._runtime = runtime

    def run(self, session: SessionState) -> None:
        if not self._runtime.books_enrichment_available():
            self._store.append_step_artifact(
                session,
                "knowledge",
                {"skipped": True, "reason": "books MCP unavailable"},
            )
            return
        asyncio.run(self._run_async(session))

    async def _run_async(self, session: SessionState) -> None:
        path = self._settings.mcp_registry_path
        data = load_registry(path)
        entry = next((e for e in data.entries if e.id == "books" and e.enabled), None)
        if entry is None:
            return
        cwd = resolve_cwd(entry.cwd, self._settings.monorepo_root)
        merged_env = {**get_default_environment(), **entry.env}
        cmd = entry.command[0]
        args = entry.command[1:] if len(entry.command) > 1 else []
        params = StdioServerParameters(command=cmd, args=args, cwd=cwd, env=merged_env)
        query = session.problem_statement
        max_books = self._settings.orch_books_enrichment_max
        names: list[str] = []
        bodies: list[tuple[str, str]] = []
        try:
            async with stdio_client(params) as streams:
                read, write = streams
                async with ClientSession(read, write) as mcp_session:
                    await mcp_session.initialize()
                    find_res = await mcp_session.call_tool(
                        "find_books",
                        {"query": query},
                    )
                    raw = _tool_text(find_res)
                    names = json.loads(raw)
                    if not isinstance(names, list):
                        names = []
                    names = [str(n) for n in names]
                    names = sorted(names)[:max_books]
                    for name in names:
                        get_res = await mcp_session.call_tool(
                            "get_book",
                            {"book_name": name},
                        )
                        bodies.append((name, _tool_text(get_res)))
        except Exception as exc:
            logger.warning("Knowledge enrichment failed: %s", exc, exc_info=True)
            self._store.append_step_artifact(
                session,
                "knowledge",
                {"error": str(exc), "query": query},
            )
            return

        lines = [f"## {title}\n\n{body}" for title, body in bodies]
        block = "\n\n".join(lines) if lines else "(No matching books.)"
        content = block
        turn = TurnRecord(
            role=TurnRole.ASSISTANT,
            kind="knowledge",
            content=content,
        )
        session.conversation_history.append(turn)
        self._store.append_step_artifact(
            session,
            "knowledge",
            {
                "query": query,
                "books": names,
                "bodies_preview": [{"name": n, "len": len(b)} for n, b in bodies],
            },
        )
