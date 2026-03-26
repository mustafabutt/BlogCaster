# SPEC-006: Platform Registry

## Title
Platform Registry — JSON-based blog platform configuration

## Description
A JSON file that stores all registered blog platforms. The orchestrator reads this file to discover platforms, their RSS feed URLs, and their base URLs for auto-detection. Adding a new platform requires only a new entry in this file — no code changes.

## File Location
`registry/platforms_registry.json`

## Format
```json
{
  "platforms": [
    {
      "id": "aspose",
      "name": "Aspose Blog",
      "url": "https://blog.aspose.com",
      "rss_feed": "https://blog.aspose.com/feed",
      "active": true
    }
  ]
}
```

## Field Definitions
| Field | Type | Required | Description |
|---|---|---|---|
| id | string | yes | Unique platform identifier, used in --platform flag |
| name | string | yes | Human-readable platform name |
| url | string | yes | Base URL of the blog, used for auto-detection from post URLs |
| rss_feed | string | yes | Full URL to the RSS feed |
| active | boolean | yes | Whether the platform is active (inactive platforms are skipped) |

## Helper Functions (in orchestrator or utils)

### `load_registry() -> dict`
- Reads and parses `platforms_registry.json`
- Returns the full registry object

### `find_platform_by_id(platform_id: str) -> dict | None`
- Finds a platform by its ID
- Returns None if not found

### `detect_platform_from_url(url: str) -> dict | None`
- Matches a blog post URL against registered platform base URLs
- Returns the matching platform or None

### `get_active_platforms() -> list`
- Returns all platforms where `active == true`

## Acceptance Criteria
- [ ] Registry file is valid JSON with the specified format
- [ ] All three initial platforms registered (aspose, groupdocs, conholdate)
- [ ] Helper functions handle missing file, invalid JSON, empty platforms list
- [ ] Platform detection works with URL prefixes (blog.aspose.com matches any post URL under it)
- [ ] Adding a new platform requires only a new JSON entry

## Dependencies
- None

## Edge Cases
- Registry file doesn't exist
- Registry file is invalid JSON
- Platform ID not found in registry
- Multiple platforms match the same URL prefix (pick first match)
- URL doesn't match any platform (return None, let caller decide)

## Out of Scope
- Web-based registry management
- Platform validation (checking if RSS feed is actually valid)
- Dynamic platform discovery
