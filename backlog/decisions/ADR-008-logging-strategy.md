# ADR-008: Logging Strategy

## Status
Accepted

## Context
The agent must log everything to `logs/logs.txt` with timestamps. Logs should capture the full pipeline execution for debugging and auditing — which posts were fetched, which were skipped (duplicates), what the LLM generated, and whether LinkedIn posting succeeded or failed.

## Decision
Use Python's built-in `logging` module with a centralized logger configuration. All components log to the same file.

### Logger Setup
File: `agent_engine/social_agent/utils/helpers.py`

```python
import logging
import os
from datetime import datetime

def setup_logger(log_path: str = "logs/logs.txt") -> logging.Logger:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger("social_agent")
    logger.setLevel(logging.DEBUG)

    # File handler — all logs
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)

    # Console handler — INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

### Log Format
```
2026-03-16 10:00:00 | INFO     | social_agent | Starting Manual Mode for URL: https://blog.aspose.com/some-post
2026-03-16 10:00:01 | INFO     | social_agent | Platform detected: aspose
2026-03-16 10:00:02 | INFO     | social_agent | Record check: not published yet
2026-03-16 10:00:03 | DEBUG    | social_agent | Fetched post: "How to Convert PDF to Word" (523 chars)
2026-03-16 10:00:05 | INFO     | social_agent | LLM formatted post (187 words)
2026-03-16 10:00:07 | INFO     | social_agent | LinkedIn post successful: post_id=xxx
2026-03-16 10:00:07 | INFO     | social_agent | Record saved for https://blog.aspose.com/some-post
```

### What to Log
| Level | What |
|---|---|
| DEBUG | Raw RSS data, LLM prompts, full API responses |
| INFO | Mode started, platform detected, post selected, post result, record saved |
| WARNING | URL doesn't match any platform, no unpublished posts found, token near expiry |
| ERROR | MCP connection failed, LLM error, LinkedIn API error, file I/O error |

### What Was Not Chosen
- **Structured logging (JSON)**: Overkill for a CLI tool with file-based logs. Plain text is easier to read.
- **Log rotation**: Not needed at current scale. Can be added later if logs grow large.
- **Third-party logging (loguru)**: Python's built-in logging is sufficient and has no dependencies.

## Consequences
- Single log file grows over time — acceptable for expected usage
- Console output keeps the user informed during execution
- Debug-level logs in file provide full audit trail
- MCP servers log independently to their own stderr — only orchestrator logs go to `logs.txt`

## Implementation Notes
- Call `setup_logger()` once in `main.py` at startup
- All modules get their logger via `logging.getLogger("social_agent")`
- MCP servers use their own loggers (stderr) — only orchestrator-level events go to logs.txt
- Log file path is configurable via settings

## References
- SPEC-004
