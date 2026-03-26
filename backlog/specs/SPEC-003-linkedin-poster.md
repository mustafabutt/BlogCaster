# SPEC-003: LinkedIn Poster MCP Server

## Title
LinkedIn Poster — FastMCP server for posting content to LinkedIn personal profile

## Description
A FastMCP server that posts formatted content to a user's LinkedIn personal profile using the LinkedIn API with a pre-generated OAuth 2.0 access token. The token is read from environment variables via config.

## Tools to Expose

### 1. `post_to_linkedin(content: str, blog_url: str) -> dict`
- Posts the formatted content to the authenticated user's LinkedIn personal profile
- `content` is the LLM-formatted LinkedIn post text
- `blog_url` is included for logging/tracking purposes
- Returns: `{ status: "success"|"failure", post_id: str, error: str|null }`
- Uses LinkedIn UGC Post API or Share API for personal profiles

### 2. `validate_token() -> bool`
- Checks if the current OAuth access token is still valid
- Makes a lightweight API call to LinkedIn (e.g., /me endpoint)
- Returns `true` if valid, `false` if expired or invalid
- Should be called before attempting to post

## Acceptance Criteria
- [ ] Both tools are registered and callable via FastMCP stdio
- [ ] Token is read from environment variable, never hardcoded
- [ ] `post_to_linkedin` returns structured response with status and post_id
- [ ] `validate_token` correctly detects expired or invalid tokens
- [ ] API errors (rate limits, network issues) return structured error responses
- [ ] Content is posted as a text post to personal profile (not company page)
- [ ] Each tool has type hints and docstring

## Dependencies
- `LINKEDIN_ACCESS_TOKEN` environment variable must be set

## Edge Cases
- Token is expired (401 response from LinkedIn)
- Token has insufficient permissions
- LinkedIn API rate limit exceeded (429 response)
- Network timeout during posting
- Content exceeds LinkedIn's character limit
- Empty content string passed to post function

## Out of Scope
- OAuth 2.0 token generation/refresh flow
- Company page posting
- Image or media attachments
- LinkedIn article publishing (long-form)
- Scheduling posts for future times
