# ADR-004: LinkedIn Poster MCP Server Design

## Status
Accepted

## Context
The agent needs to post formatted text content to a user's personal LinkedIn profile. LinkedIn provides a REST API for creating posts (UGC Posts / Shares). Authentication uses OAuth 2.0, and we have a pre-generated access token.

## Decision
Build a LinkedIn Poster as a FastMCP server with two tools, using `httpx` for HTTP requests to the LinkedIn API.

### Tools
1. **`post_to_linkedin(content: str, blog_url: str) -> dict`** — Create a text post on personal profile
2. **`validate_token() -> bool`** — Check if the access token is still valid

### LinkedIn API Details

#### Authentication
- OAuth 2.0 Bearer token from `LINKEDIN_ACCESS_TOKEN` env var
- Header: `Authorization: Bearer {token}`

#### Get User Profile (for validate_token and user ID)
- `GET https://api.linkedin.com/v2/userinfo`
- Returns user profile including `sub` (member ID)
- Used to validate token and get the `author` URN for posts

#### Create Post
- `POST https://api.linkedin.com/rest/posts`
- Headers:
  - `Authorization: Bearer {token}`
  - `Content-Type: application/json`
  - `LinkedIn-Version: 202401`
  - `X-Restli-Protocol-Version: 2.0.0`
- Body:
```json
{
  "author": "urn:li:person:{member_id}",
  "lifecycleState": "PUBLISHED",
  "visibility": "PUBLIC",
  "commentary": "{formatted_post_text}",
  "distribution": {
    "feedDistribution": "MAIN_FEED",
    "targetEntities": [],
    "thirdPartyDistributionChannels": []
  }
}
```

#### Response Handling
- 201 Created → success, extract post ID from `x-restli-id` header or response
- 401 Unauthorized → token expired
- 403 Forbidden → insufficient permissions
- 429 Too Many Requests → rate limited

### What Was Not Chosen
- **LinkedIn SDK/wrapper library**: No well-maintained official Python SDK. Raw HTTP calls via httpx are cleaner and give full control.
- **Company page posting**: Out of scope — personal profile only.
- **OAuth flow**: Token is pre-generated — no need for authorization code flow.

## Consequences
- Token must be manually refreshed when it expires (no auto-refresh)
- The `validate_token` tool should be called before posting to fail fast
- LinkedIn API has rate limits — the agent should log rate limit responses clearly
- Personal profile posting requires `w_member_social` OAuth scope on the token

## Implementation Notes
- Server file: `mcp-servers/linkedin-poster/server.py`
- Dependencies: `fastmcp`, `httpx`
- All HTTP calls are async
- Timeout: 30 seconds for API calls
- Cache the member ID after first fetch (avoid repeated /userinfo calls)
- Log full API responses at debug level for troubleshooting

## References
- SPEC-003
