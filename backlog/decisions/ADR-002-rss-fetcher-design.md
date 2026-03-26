# ADR-002: RSS Fetcher MCP Server Design

## Status
Accepted

## Context
The agent needs to fetch blog posts from Hugo-based blog platforms. Hugo blogs expose RSS feeds (typically at `/feed` or `/index.xml`). The fetcher must support two access patterns:
1. Fetch a list of recent posts from an RSS feed (Auto Mode)
2. Fetch a single post by its direct URL (Manual Mode)

## Decision
Build an RSS Fetcher as a FastMCP server with three tools, using `feedparser` for RSS parsing and `httpx` for HTTP requests with `beautifulsoup4` for HTML parsing.

### Tools
1. **`fetch_rss(platform_url: str) -> dict`** — Full feed parse, returns metadata + all items
2. **`get_latest_posts(platform_url: str, limit: int = 10) -> list`** — Clean list of recent posts, sorted newest first
3. **`fetch_post_by_url(url: str) -> dict`** — Single post fetch by URL, extracts title + content from HTML page

### Libraries
- **`feedparser`** — Standard Python RSS/Atom parser. Handles RSS 2.0 and Atom feeds, tolerant of malformed XML.
- **`httpx`** — Async HTTP client. Used for fetching feed URLs and individual blog post pages.
- **`beautifulsoup4`** — HTML parser. Used to extract content from individual blog post pages and to strip HTML tags from RSS summaries.

### HTML Stripping Strategy
- RSS summaries: Strip HTML using BeautifulSoup's `get_text()` method
- Individual posts: Extract content from `<article>` or `<div class="content">` tags (Hugo standard), then strip HTML
- Always return clean plain text to the caller

### Error Handling
- Network errors → return `{"error": "...", "status": "failed"}`
- Empty feeds → return empty list, not error
- Missing fields → use defaults (empty string for summary, "Unknown" for title)

## Consequences
- `feedparser` is a well-maintained library but may struggle with non-standard feeds
- `fetch_post_by_url` depends on Hugo's HTML structure — may need adjustment for custom Hugo themes
- All content is returned as plain text — no HTML passes through to the LLM

## Implementation Notes
- Server file: `mcp-servers/rss-fetcher/server.py`
- Dependencies: `fastmcp`, `feedparser`, `httpx`, `beautifulsoup4`
- All functions are async
- Timeout: 30 seconds for HTTP requests
- User-Agent header should be set to avoid blocks

## References
- SPEC-001
