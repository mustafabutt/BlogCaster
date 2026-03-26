# ADR-003: Record Keeper MCP Server Design

## Status
Accepted

## Context
The agent must never post the same blog URL twice. A record-keeping system is needed to track all published posts, queryable by URL and platform. The storage must be simple (no database), human-readable, and accessible by a future web UI.

## Decision
Build a Record Keeper as a FastMCP server with four tools, using a JSON file as the persistence layer.

### Tools
1. **`is_published(blog_url: str) -> bool`** — Duplicate check
2. **`save_record(blog_url: str, title: str, platform_id: str, results: dict) -> bool`** — Save posting result
3. **`get_records() -> list`** — Return all records
4. **`get_records_by_platform(platform_id: str) -> list`** — Filter by platform

### Storage
- File: `content/records/published_record.json`
- Format: `{"records": [...]}`
- Each record: `{blog_url, title, platform_id, shared_on: {linkedin: {status, post_id, shared_at}}}`

### URL Normalization
Before checking or saving, normalize blog URLs:
- Strip trailing slashes
- Remove query parameters and fragments
- Lowercase the URL
This prevents duplicates like `https://blog.aspose.com/post/` vs `https://blog.aspose.com/post`

### File Safety
- Read the full file, modify in memory, write back atomically
- Use a temporary file + rename pattern for atomic writes
- Create file with empty `{"records": []}` structure if it doesn't exist
- Handle corrupted JSON by logging error and starting fresh (with backup of corrupted file)

### What Was Not Chosen
- **SQLite**: Adds complexity. JSON is sufficient for the expected volume (hundreds of records, not millions).
- **In-memory only**: Would lose state between runs.
- **CSV**: Harder to represent nested structures (shared_on with per-platform results).

## Consequences
- JSON file grows linearly — acceptable for expected volume
- No concurrent write safety beyond atomic file writes (sufficient for single CLI process)
- Future web UI reads the same JSON file — no adapter needed
- URL normalization means the system is forgiving of URL variations

## Implementation Notes
- Server file: `mcp-servers/record-keeper/server.py`
- Dependencies: `fastmcp`, `aiofiles`
- Record file path should be configurable via settings, defaulting to `content/records/published_record.json`
- All file I/O is async
- Timestamps in ISO 8601 format: `YYYY-MM-DD HH:MM:SS`

## References
- SPEC-002
