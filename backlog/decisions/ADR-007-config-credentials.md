# ADR-007: Configuration and Credentials Management

## Status
Accepted

## Context
The agent requires several configuration values: LLM API credentials, LinkedIn access token, file paths, and other settings. These must never be hardcoded. The user's existing agents use Pydantic `BaseSettings` with `.env` files.

## Decision
Use **Pydantic `BaseSettings`** with a `.env` file for all configuration. A single `config.py` module serves as the centralized config source.

### Config Module
File: `agent_engine/social_agent/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Configuration
    PROFESSIONALIZE_BASE_URL: str
    PROFESSIONALIZE_API_KEY_2: str
    PROFESSIONALIZE_LLM_MODEL: str

    # LinkedIn Configuration
    LINKEDIN_ACCESS_TOKEN: str

    # File Paths (with defaults)
    REGISTRY_PATH: str = "registry/platforms_registry.json"
    RECORDS_PATH: str = "content/records/published_record.json"
    LOG_PATH: str = "logs/logs.txt"

    # MCP Server Paths (with defaults)
    RSS_FETCHER_PATH: str = "mcp-servers/rss-fetcher/server.py"
    LINKEDIN_POSTER_PATH: str = "mcp-servers/linkedin-poster/server.py"
    RECORD_KEEPER_PATH: str = "mcp-servers/record-keeper/server.py"

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
```

### .env File
```
PROFESSIONALIZE_BASE_URL=https://your-gpt-oss-endpoint.com/v1
PROFESSIONALIZE_API_KEY_2=your-api-key
PROFESSIONALIZE_LLM_MODEL=your-model-name
LINKEDIN_ACCESS_TOKEN=your-linkedin-token
```

### What Was Not Chosen
- **config.json / config.yaml**: Less standard for Python projects. `.env` is the convention for secrets and Pydantic supports it natively.
- **Environment variables only (no file)**: `.env` file is more convenient for development. Pydantic reads both the file and actual env vars (env vars take precedence).
- **dotenv library**: Pydantic BaseSettings handles `.env` loading natively — no need for `python-dotenv`.

## Consequences
- All config in one place — easy to review and audit
- `.env` file must be in `.gitignore` to prevent credential leaks
- Default paths use relative paths — assumes the CLI is run from the project root
- MCP servers that need config (e.g., linkedin-poster) will receive credentials via environment variables passed through subprocess

## Implementation Notes
- Create `.env.example` with placeholder values (committed to git)
- Add `.env` to `.gitignore`
- Import `settings` from `config.py` wherever config is needed
- For MCP server subprocesses, pass relevant env vars via `StdioServerParameters.env`
- File paths should be resolved relative to the project root

## References
- SPEC-004, SPEC-005
