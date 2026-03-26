# Social Media Agent

A CLI-based agent that fetches blog posts from Hugo-based blog platforms via RSS feeds, formats them into professional LinkedIn posts using an LLM, and publishes them to a personal LinkedIn profile.

The agent is platform-driven — each blog platform is registered in a JSON registry and the agent can operate independently per platform. Adding a new blog platform requires only a new entry in the registry file, no code changes.

## How It Works

```
RSS Feed ──> Record Check ──> Post Selection ──> LLM Formatting ──> LinkedIn Post ──> Record Save
```

Three FastMCP servers handle the core operations, coordinated by a central orchestrator:

| MCP Server | Role |
|---|---|
| **rss-fetcher** | Fetches and parses Hugo RSS feeds and individual blog posts |
| **record-keeper** | Tracks published posts in JSON, prevents duplicates |
| **linkedin-poster** | Posts formatted content to LinkedIn personal profile |

## Two Operating Modes

### Manual Mode

Provide a specific blog post URL. The agent auto-detects the platform, fetches the content, formats it, posts it to LinkedIn, and records the result.

```bash
python -m agent_engine.social_agent.main --url "https://blog.aspose.com/some-post"
```

### Auto Mode

Specify a platform ID. The agent fetches the RSS feed, picks the latest unpublished post, formats it, posts it to LinkedIn, and records the result.

```bash
python -m agent_engine.social_agent.main --auto --platform aspose
python -m agent_engine.social_agent.main --auto --platform groupdocs
python -m agent_engine.social_agent.main --auto --platform conholdate
```

## Prerequisites

- Python 3.10+
- A self-hosted GPT-OSS LLM endpoint (OpenAI-compatible API)
- A LinkedIn OAuth 2.0 access token with `w_member_social` scope

## Setup

### 1. Clone and navigate to the project

```bash
cd socialAgent
```

### 2. Install dependencies

```bash
pip install mcp feedparser httpx beautifulsoup4 aiofiles pydantic-settings openai
```

### 3. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
# LLM Configuration (GPT-OSS)
PROFESSIONALIZE_BASE_URL=https://your-gpt-oss-endpoint.com/v1
PROFESSIONALIZE_API_KEY_2=your-api-key
PROFESSIONALIZE_LLM_MODEL=your-model-name

# LinkedIn Configuration
LINKEDIN_ACCESS_TOKEN=your-linkedin-oauth-token
```

| Variable | Description |
|---|---|
| `PROFESSIONALIZE_BASE_URL` | Base URL of your OpenAI-compatible LLM endpoint |
| `PROFESSIONALIZE_API_KEY_2` | API key for the LLM endpoint |
| `PROFESSIONALIZE_LLM_MODEL` | Model name to use for text generation |
| `LINKEDIN_ACCESS_TOKEN` | Pre-generated LinkedIn OAuth 2.0 access token |

## Usage

All commands must be run from the project root directory.

### Post a specific blog URL (Manual Mode)

```bash
python -m agent_engine.social_agent.main --url "https://blog.aspose.com/some-post"
```

### Post the latest unposted blog from a platform (Auto Mode)

```bash
python -m agent_engine.social_agent.main --auto --platform aspose
```

### List available platforms

```bash
python -m agent_engine.social_agent.main --auto
```

Output:

```
Error: --platform is required with --auto

Available platforms:
  - aspose          (Aspose Blog)
  - groupdocs       (GroupDocs Blog)
  - conholdate      (Conholdate Blog)
```

### Show usage help

```bash
python -m agent_engine.social_agent.main
```

## Adding a New Blog Platform

Edit `registry/platforms_registry.json` and add a new entry:

```json
{
  "id": "your-platform",
  "name": "Your Platform Blog",
  "url": "https://blog.yourplatform.com",
  "rss_feed": "https://blog.yourplatform.com/index.xml",
  "active": true
}
```

No code changes required. The new platform is immediately available:

```bash
python -m agent_engine.social_agent.main --auto --platform your-platform
```

## Project Structure

```
socialAgent/
├── agent_engine/
│   └── social_agent/
│       ├── main.py                  # CLI entry point
│       ├── config.py                # Pydantic BaseSettings config
│       ├── agent_logic/
│       │   └── orchestrator.py      # Core workflow (manual + auto modes)
│       ├── tools/
│       │   └── mcp_tools.py         # MCP server wrappers
│       └── utils/
│           ├── helpers.py           # Logger setup + registry helpers
│           ├── llm_service.py       # LLM formatting via OpenAI SDK
│           └── prompts.py           # LinkedIn post prompt templates
├── mcp-servers/
│   ├── rss-fetcher/server.py        # RSS feed parsing (feedparser + httpx + bs4)
│   ├── linkedin-poster/server.py    # LinkedIn API posting (httpx)
│   └── record-keeper/server.py      # JSON-based record storage (aiofiles)
├── registry/
│   └── platforms_registry.json      # Blog platform registry
├── content/
│   └── records/
│       └── published_record.json    # Published post records
├── logs/
│   └── logs.txt                     # Application logs
├── .env                             # Credentials (not committed)
├── .env.example                     # Credential template
└── .gitignore
```

## Logs

All operations are logged to `logs/logs.txt` with timestamps. Console output shows INFO-level messages, the log file captures DEBUG-level detail.

```
2026-03-17 03:28:49 | INFO     | social_agent | Starting Auto Mode for platform: aspose
2026-03-17 03:28:50 | INFO     | social_agent | Fetched 10 posts from RSS feed
2026-03-17 03:28:51 | INFO     | social_agent | Selected unpublished post: "Convert OneNote..." — https://...
2026-03-17 03:28:58 | INFO     | social_agent | LLM formatted post (102 words)
2026-03-17 03:29:01 | INFO     | social_agent | LinkedIn post successful: post_id=urn:li:share:...
2026-03-17 03:29:01 | INFO     | social_agent | Record saved for https://...
```

## Duplicate Prevention

The agent never posts the same blog URL twice. Before posting, it always checks the record keeper. URLs are normalized (lowercased, trailing slashes stripped, query parameters removed) to catch variations like:

- `https://blog.aspose.com/post/` vs `https://blog.aspose.com/post`
- `https://blog.aspose.com/post?utm=123` vs `https://blog.aspose.com/post`

## LinkedIn Post Format

The LLM generates posts with:

- Professional tone
- 150-200 words
- Hook line that grabs attention
- 3-5 relevant hashtags
- Blog URL at the end

## Troubleshooting

| Issue | Solution |
|---|---|
| `PROFESSIONALIZE_BASE_URL is not set` | Create `.env` file from `.env.example` and fill in LLM credentials |
| `LinkedIn token is expired or invalid (401)` | Generate a new LinkedIn OAuth token and update `.env` |
| `Insufficient permissions (403)` | Ensure your LinkedIn token has `w_member_social` scope |
| `All recent posts have already been shared` | All RSS feed posts are already in the record — wait for new blog posts |
| `Platform 'xxx' not found` | Check `registry/platforms_registry.json` for available platform IDs |

## Future Extensibility

| Goal | Change Required |
|---|---|
| Add a new blog platform | New entry in `registry/platforms_registry.json` |
| Add Twitter/X posting | New MCP server in `mcp-servers/twitter-poster/` |
| Add a web UI | FastAPI layer wrapping the existing MCP tools |
| Switch to a database | Replace `record-keeper/server.py` internals (same MCP interface) |
