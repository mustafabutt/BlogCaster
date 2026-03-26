# SPEC-004: Orchestrator and CLI Entry Point

## Title
Orchestrator and CLI — Core workflow engine and command-line interface

## Description
The orchestrator implements the core agent workflow for both Manual and Auto modes. The CLI (`main.py`) parses arguments and delegates to the orchestrator. The orchestrator coordinates all MCP servers and the LLM formatter to execute the full post-publishing pipeline.

## CLI Interface

### Manual Mode
```
python main.py --url "https://blog.aspose.com/some-post"
```

### Auto Mode
```
python main.py --auto --platform aspose
```

### Error Cases
```
python main.py --auto              # Error: --platform required, list available platforms
python main.py                     # Print usage instructions and exit
```

## Orchestrator Workflows

### Manual Mode Flow
1. Receive URL from CLI
2. Auto-detect `platform_id` from URL against `platforms_registry.json`
3. Call Record Keeper → `is_published(url)` — stop if already posted
4. Call RSS Fetcher → `fetch_post_by_url(url)` — get title + summary
5. Call LLM Formatter → generate LinkedIn post from content
6. Call LinkedIn Poster → `post_to_linkedin(formatted_content, url)`
7. Call Record Keeper → `save_record(url, title, platform_id, results)`
8. Log everything to `logs/logs.txt`

### Auto Mode Flow
1. Load `platforms_registry.json` → find platform by ID
2. Validate platform exists and `active == true` — stop if not
3. Call RSS Fetcher → `get_latest_posts(platform_rss_url)`
4. Call Record Keeper → `is_published()` for each post — filter out already posted
5. Pick first unpublished post (newest first)
6. Call LLM Formatter → generate LinkedIn post from content
7. Call LinkedIn Poster → `post_to_linkedin(formatted_content, blog_url)`
8. Call Record Keeper → `save_record(url, title, platform_id, results)`
9. Log everything to `logs/logs.txt`

## Acceptance Criteria
- [ ] CLI correctly parses --url, --auto, --platform flags
- [ ] Manual mode auto-detects platform from URL
- [ ] Auto mode validates platform exists and is active
- [ ] Both modes check record-keeper before posting
- [ ] LLM formatter is called with proper prompt for LinkedIn format
- [ ] All MCP server calls use stdio transport
- [ ] Errors at any step are logged and execution stops gracefully
- [ ] Usage instructions printed when no args provided
- [ ] Error message + available platforms printed when --auto without --platform
- [ ] All steps logged to logs/logs.txt with timestamps

## Dependencies
- SPEC-001 (RSS Fetcher MCP)
- SPEC-002 (Record Keeper MCP)
- SPEC-003 (LinkedIn Poster MCP)
- SPEC-005 (LLM Formatter)
- SPEC-006 (Platform Registry)

## Edge Cases
- URL doesn't match any registered platform (warn but proceed in manual mode)
- No unpublished posts found in auto mode (log and exit gracefully)
- LLM formatter returns empty or invalid content
- MCP server connection failure
- Platform ID not found in registry
- Platform exists but `active == false`

## Out of Scope
- Interactive mode / REPL
- Web-based interface
- Batch processing multiple platforms in one run
- Retry logic for failed posts (log and exit)
