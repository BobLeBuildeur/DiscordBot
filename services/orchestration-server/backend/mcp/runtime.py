from __future__ import annotations

import logging
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, get_default_environment, stdio_client

from backend.config import Settings
from backend.mcp.models import DiscoveredMcpServer, McpRegistryEntry
from backend.mcp.registry import load_registry, resolve_cwd

logger = logging.getLogger(__name__)


class McpRegistryRuntime:
    """Cached MCP discovery results keyed by server id."""

    def __init__(self, servers: dict[str, DiscoveredMcpServer]) -> None:
        self._servers = servers

    def get(self, server_id: str) -> DiscoveredMcpServer | None:
        return self._servers.get(server_id)

    def books_enrichment_available(self) -> bool:
        b = self._servers.get("books")
        return b is not None and b.available


async def discover_registry(settings: Settings) -> McpRegistryRuntime:
    path = settings.mcp_registry_path
    if not path.exists():
        logger.warning("MCP registry not found at %s; skipping discovery.", path)
        return McpRegistryRuntime({})

    data = load_registry(path)
    servers: dict[str, DiscoveredMcpServer] = {}
    for entry in data.entries:
        if not entry.enabled:
            servers[entry.id] = DiscoveredMcpServer(
                id=entry.id, available=False, error="disabled in registry"
            )
            continue
        discovered = await _discover_one(entry, settings.monorepo_root)
        servers[entry.id] = discovered
        if discovered.available:
            logger.info(
                "MCP server %r discovered: %d tools, %d resources",
                entry.id,
                len(discovered.tool_names),
                len(discovered.resource_uris),
            )
        else:
            logger.warning("MCP server %r unavailable: %s", entry.id, discovered.error)
    return McpRegistryRuntime(servers)


async def _discover_one(entry: McpRegistryEntry, monorepo_root: Path) -> DiscoveredMcpServer:
    cwd = resolve_cwd(entry.cwd, monorepo_root)
    base_env = get_default_environment()
    merged_env = {**base_env, **entry.env}
    cmd = entry.command[0]
    args = entry.command[1:] if len(entry.command) > 1 else []
    params = StdioServerParameters(command=cmd, args=args, cwd=cwd, env=merged_env)
    try:
        async with stdio_client(params) as streams:
            read, write = streams
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                try:
                    resources_result = await session.list_resources()
                except Exception as res_exc:
                    logger.warning("list_resources failed for %s: %s", entry.id, res_exc)
                    resources_result = None
        tool_names = [t.name for t in tools_result.tools]
        resource_uris: list[str] = []
        if resources_result is not None:
            for r in resources_result.resources:
                if hasattr(r, "uri"):
                    resource_uris.append(str(r.uri))
        return DiscoveredMcpServer(
            id=entry.id,
            available=True,
            tool_names=tool_names,
            resource_uris=resource_uris,
            error=None,
        )
    except Exception as exc:
        logger.exception("MCP discovery failed for %s", entry.id)
        return DiscoveredMcpServer(
            id=entry.id,
            available=False,
            error=str(exc),
        )
