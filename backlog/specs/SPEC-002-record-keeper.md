# SPEC-002: Record Keeper MCP Server

## Title
Record Keeper — FastMCP server for tracking published blog posts

## Description
A FastMCP server that manages a JSON-based record of all blog posts that have been shared to social media. Provides tools to check if a post has already been published, save new records, and retrieve records. All state is stored in `content/records/published_record.json`.

## Tools to Expose

### 1. `is_published(blog_url: str) -> bool`
- Checks if the given blog URL exists in the published record
- Returns `true` if already posted, `false` otherwise
- Used by both Manual and Auto modes before posting

### 2. `save_record(blog_url: str, title: str, platform_id: str, results: dict) -> bool`
- Saves a new posting record to the JSON file
- `results` contains per-platform posting outcomes (e.g., LinkedIn status, post_id, timestamp)
- Returns `true` on success, `false` on failure
- Creates the JSON file if it doesn't exist
- Thread-safe file writes

### 3. `get_records() -> list`
- Returns all records from the published record file
- Returns empty list if no records exist
- REST-ready for future web UI consumption

### 4. `get_records_by_platform(platform_id: str) -> list`
- Returns records filtered by the given platform ID
- Returns empty list if no records match

## Acceptance Criteria
- [ ] All four tools are registered and callable via FastMCP stdio
- [ ] JSON file is created automatically if it doesn't exist
- [ ] `is_published` correctly identifies duplicate URLs
- [ ] `save_record` appends to existing records without overwriting
- [ ] Records include timestamp of when they were saved
- [ ] File I/O errors return structured responses, not exceptions
- [ ] Each tool has type hints and docstring

## Record Format
```json
{
  "records": [
    {
      "blog_url": "https://blog.aspose.com/some-post",
      "title": "How to Convert PDF to Word",
      "platform_id": "aspose",
      "shared_on": {
        "linkedin": {
          "status": "success",
          "post_id": "xxx",
          "shared_at": "2026-03-10 10:00:00"
        }
      }
    }
  ]
}
```

## Dependencies
- None (standalone MCP server)

## Edge Cases
- JSON file doesn't exist yet (first run)
- JSON file is corrupted or empty
- Concurrent writes to the same file
- Blog URL with trailing slashes or query params (normalize before checking)
- `save_record` called with a URL that already exists (should not create duplicate)

## Out of Scope
- Database storage (JSON only for now)
- Record deletion or editing
- Web UI endpoints (functions are REST-ready but no HTTP layer)
