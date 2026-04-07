"""Books MCP: find + fetch book bodies for the problem statement on new sessions."""

from __future__ import annotations

import asyncio
import json
import logging

from mcp import ClientSession

from backend.config import Settings
from backend.mcp.registry import load_registry
from backend.mcp.runtime import McpRegistryRuntime
from backend.mcp.stdio_client import tool_result_text, with_mcp_session
from backend.orchestrator.models import SessionState, TurnRecord, TurnRole
from backend.orchestrator.store import FileBackedSessionStore

logger = logging.getLogger(__name__)


class BooksKnowledgeForNewSession:
    """After the first user turn, add a silent `knowledge` turn from books MCP (if available)."""

    def __init__(
        self,
        settings: Settings,
        store: FileBackedSessionStore,
        runtime: McpRegistryRuntime,
    ) -> None:
        self._settings = settings
        self._store = store
        self._runtime = runtime

    def __call__(self, session: SessionState) -> None:
        if not self._runtime.server_offers_tools("books", "find_books", "get_book"):
            self._store.append_step_artifact(
                session,
                "knowledge",
                {"skipped": True, "reason": "books MCP unavailable or missing tools"},
            )
            return
        asyncio.run(self._run_async(session))

    async def _run_async(self, session: SessionState) -> None:
        path = self._settings.mcp_registry_path
        data = load_registry(path)
        entry = next((e for e in data.entries if e.id == "books" and e.enabled), None)
        if entry is None:
            return
        query = session.problem_statement
        max_books = self._settings.orch_books_knowledge_max
        names: list[str] = []
        bodies: list[tuple[str, str]] = []
        try:

            async def fetch(mcp: ClientSession) -> None:
                nonlocal names
                find_res = await mcp.call_tool("find_books", {"query": query})
                raw = tool_result_text(find_res)
                names = json.loads(raw)
                if not isinstance(names, list):
                    names = []
                names = [str(n) for n in names]
                names = sorted(names)[:max_books]
                for name in names:
                    get_res = await mcp.call_tool("get_book", {"book_name": name})
                    bodies.append((name, tool_result_text(get_res)))

            await with_mcp_session(entry, self._settings.monorepo_root, fetch)
        except Exception as exc:
            logger.warning("Books knowledge hook failed: %s", exc, exc_info=True)
            self._store.append_step_artifact(
                session,
                "knowledge",
                {"error": str(exc), "query": query},
            )
            return

        lines = [f"## {title}\n\n{body}" for title, body in bodies]
        block = "\n\n".join(lines) if lines else "(No matching books.)"
        turn = TurnRecord(
            role=TurnRole.ASSISTANT,
            kind="knowledge",
            content=block,
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
