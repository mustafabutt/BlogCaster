# SPEC-001: RSS Fetcher MCP Server

## Title
RSS Fetcher — FastMCP server for fetching and parsing Hugo RSS feeds

## Description
A FastMCP server that fetches RSS feeds from Hugo-based blog platforms, parses them, and returns clean post data. Supports both fetching a list of recent posts from a feed URL and fetching a single post by its direct URL. All HTML tags must be stripped from content before returning.

## Tools to Expose

### 1. `fetch_rss(platform_url: str) -> dict`
- Fetches and parses a Hugo RSS feed from the given URL
- Returns full parsed feed metadata and list of posts
- Each post includes: title, link, summary (HTML-stripped), published date
- Handles network errors, malformed XML, and empty feeds gracefully

### 2. `get_latest_posts(platform_url: str, limit: int = 10) -> list`
- Fetches RSS feed and returns a clean list of recent posts
- Sorted by published date, newest first
- Each post: `{ title, link, summary, published_date }`
- `limit` parameter controls how many posts to return

### 3. `fetch_post_by_url(url: str) -> dict`
- Fetches a single blog post page by its URL
- Extracts: title, full content/summary, published date, author
- Strips all HTML tags from content
- Used in Manual Mode when user provides a specific blog URL

## Acceptance Criteria
- [ ] All three tools are registered and callable via FastMCP stdio
- [ ] HTML tags are fully stripped from all returned content
- [ ] Empty or truncated summaries are handled (return empty string, not error)
- [ ] Network errors return structured error responses, not exceptions
- [ ] Feed parsing handles Hugo RSS format correctly (Atom and RSS 2.0)
- [ ] Posts are sorted by published date descending
- [ ] Each tool has type hints and docstring

## Dependencies
- None (standalone MCP server)

## Edge Cases
- RSS feed URL returns 404 or 500
- RSS feed is valid XML but has no items
- Post summary is empty or contains only HTML tags
- Blog post URL returns 404
- Feed contains malformed dates
- Feed items missing required fields (title, link)

## Out of Scope
- Caching of feed results
- Pagination of feed results beyond `limit` parameter
- Authentication for private RSS feeds
