# ADR-005: Orchestrator and CLI Design

## Status
Accepted

## Context
The agent needs a CLI entry point that handles argument parsing and an orchestrator that coordinates all MCP servers and the LLM formatter. Two modes (Manual and Auto) share the same downstream tools but have different entry logic.

## Decision
Implement a two-layer design: `main.py` for CLI parsing and `orchestrator.py` for workflow coordination.

### CLI Layer (`main.py`)
- Uses Python's `argparse` for argument parsing
- Flags: `--url`, `--auto`, `--platform`
- Validates flag combinations and delegates to orchestrator
- Handles top-level exceptions and prints user-friendly error messages

#### Argument Rules
| Flags | Action |
|---|---|
| `--url <url>` | Run Manual Mode |
| `--auto --platform <id>` | Run Auto Mode for that platform |
| `--auto` (no --platform) | Print error + list available platform IDs |
| No flags | Print usage instructions |

### Orchestrator Layer (`orchestrator.py`)
- Two async functions: `run_manual_mode(url)` and `run_auto_mode(platform_id)`
- Manages MCP server connections (start/stop via stdio)
- Coordinates the full pipeline: check → fetch → format → post → record → log

### MCP Client Connection
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["mcp-servers/rss-fetcher/server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("get_latest_posts", {"platform_url": "..."})
```

### Platform Detection (Manual Mode)
- Load `platforms_registry.json`
- For each platform, check if the given URL starts with `platform.url`
- If match found, use that platform's ID
- If no match, log a warning but continue (platform_id = "unknown")

### Post Selection (Auto Mode)
- Fetch latest posts from RSS feed
- For each post (newest first), check `is_published`
- Pick the first unpublished post
- If all posts are already published, log and exit gracefully

### What Was Not Chosen
- **Click/Typer for CLI**: Overkill for 3 flags. `argparse` is stdlib and sufficient.
- **Single orchestrator function with mode parameter**: Separate functions are clearer and more maintainable.
- **Persistent MCP connections**: Start and stop per run. No need for connection pooling in a CLI tool.

## Consequences
- Each run starts fresh MCP connections (slight overhead, but simple and reliable)
- The orchestrator is the only component that knows about all MCP servers
- Adding a new social platform means adding a new MCP client call in the orchestrator
- Both modes share the LLM formatter and logging, keeping them consistent

## Implementation Notes
- Files: `agent_engine/social_agent/main.py`, `agent_engine/social_agent/agent_logic/orchestrator.py`
- Use `asyncio.run()` in main.py to enter async context
- MCP tool wrappers in `tools/mcp_tools.py` for cleaner orchestrator code
- Each MCP server path should be configurable (not hardcoded)

## References
- SPEC-004
