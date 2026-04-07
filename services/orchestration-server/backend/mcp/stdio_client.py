"""Low-level MCP STDIO session helper — transport only; no orchestration semantics."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, get_default_environment, stdio_client

from backend.mcp.models import McpRegistryEntry
from backend.mcp.registry import resolve_cwd

T = TypeVar("T")


def tool_result_text(result: object) -> str:
    """Concatenate text blocks from an MCP CallToolResult."""
    chunks: list[str] = []
    for block in result.content:
        if getattr(block, "type", None) == "text" and hasattr(block, "text"):
            chunks.append(block.text)
    return "".join(chunks)


async def with_mcp_session(
    entry: McpRegistryEntry,
    monorepo_root: Path,
    fn: Callable[[ClientSession], Awaitable[T]],
) -> T:
    """Run `fn` with a connected, initialized MCP client for one registry entry."""
    cwd = resolve_cwd(entry.cwd, monorepo_root)
    merged_env = {**get_default_environment(), **entry.env}
    cmd = entry.command[0]
    args = entry.command[1:] if len(entry.command) > 1 else []
    params = StdioServerParameters(command=cmd, args=args, cwd=cwd, env=merged_env)
    async with stdio_client(params) as streams:
        read, write = streams
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            return await fn(mcp_session)
