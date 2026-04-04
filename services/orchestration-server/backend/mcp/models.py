from __future__ import annotations

from pydantic import BaseModel, Field


class McpRegistryEntry(BaseModel):
    id: str
    enabled: bool = True
    enrichment: bool = False
    command: list[str] = Field(min_length=1)
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)


class McpRegistryFile(BaseModel):
    entries: list[McpRegistryEntry] = Field(default_factory=list)


class DiscoveredMcpServer(BaseModel):
    id: str
    available: bool
    tool_names: list[str] = Field(default_factory=list)
    resource_uris: list[str] = Field(default_factory=list)
    error: str | None = None
