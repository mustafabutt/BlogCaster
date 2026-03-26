# ADR-001: MCP Server Architecture

## Status
Accepted

## Context
The Social Media Agent requires modular, extensible components for RSS fetching, LinkedIn posting, and record keeping. These components need to be independently deployable and testable, and must support future addition of new social media platforms without modifying existing code.

We need to decide on the communication pattern and framework for these components.

## Decision
Use **FastMCP** framework with **stdio transport** for all MCP servers.

### Architecture
- Three independent FastMCP servers: rss-fetcher, linkedin-poster, record-keeper
- Each server runs as a subprocess, communicating via stdin/stdout (stdio transport)
- The orchestrator starts and manages MCP server connections
- Each server has its own `server.py` and `requirements.txt`

### Why FastMCP + stdio
- **FastMCP** is the standard Python framework for MCP servers — provides decorators, type validation, and tool registration out of the box
- **stdio transport** is the simplest for CLI tools — no HTTP server, no port management, no network configuration
- Each server is a standalone Python script that can be tested independently
- Matches the CLI-first nature of this project

### What Was Not Chosen
- **HTTP/SSE transport**: Overkill for a CLI tool. Adds complexity (ports, CORS, connection management) with no benefit for subprocess communication.
- **Direct function calls**: Would couple all components together, making it impossible to add new social platforms as independent servers.
- **gRPC**: Too heavy for this use case. FastMCP stdio is simpler and sufficient.

## Consequences
- Each MCP server must define its tools using FastMCP `@mcp.tool()` decorators
- The orchestrator must use `mcp` client library to connect to each server via stdio
- Adding a new social media platform = new FastMCP server in `mcp-servers/` directory
- All servers share the same config pattern (Pydantic BaseSettings + .env)
- Testing each server can be done by running it directly and sending JSON-RPC over stdio

## References
- SPEC-001, SPEC-002, SPEC-003
