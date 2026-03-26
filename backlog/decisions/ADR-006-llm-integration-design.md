# ADR-006: LLM Integration Design

## Status
Accepted

## Context
The agent needs to format blog post data (title, summary, URL) into professional LinkedIn posts. The LLM is a self-hosted GPT-OSS instance accessible via an OpenAI-compatible API. The user's existing agents use the OpenAI Python SDK with `AsyncOpenAI`.

## Decision
Use the **OpenAI Python SDK** (`AsyncOpenAI`) pointed at the GPT-OSS endpoint for LLM calls. Keep it as a simple service module (not an MCP server) since it's an internal utility, not an externally callable tool.

### Architecture
- Module: `agent_engine/social_agent/utils/llm_service.py`
- Prompt templates: `agent_engine/social_agent/utils/prompts.py`
- Uses singleton pattern matching the user's existing `LLMService` implementation

### LLM Service
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url=settings.PROFESSIONALIZE_BASE_URL,
    api_key=settings.PROFESSIONALIZE_API_KEY_2
)

response = await client.chat.completions.create(
    model=settings.PROFESSIONALIZE_LLM_MODEL,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7,
    max_tokens=1000
)
```

### Prompt Strategy
- System prompt: Define the role (LinkedIn content writer) and format rules
- User prompt: Provide the blog title, summary, and URL
- Format rules in prompt:
  - Professional tone
  - 150-200 words
  - Start with a hook line
  - 3-5 relevant hashtags at the end
  - Include blog URL at the end
  - No markdown formatting in output

### What Was Not Chosen
- **LLM as MCP server**: Unnecessary indirection. The LLM is an internal utility used only by the orchestrator. Making it an MCP server adds complexity without extensibility benefit.
- **LangChain / LlamaIndex**: Heavy frameworks for a simple completion call. Direct OpenAI SDK is simpler and matches existing patterns.
- **Agent-based LLM (multi-turn)**: Simple single-turn completion is sufficient for text formatting. No need for agent loops.

## Consequences
- Simple, predictable LLM calls with no framework overhead
- Prompt quality directly determines output quality — prompts should be iterated
- If GPT-OSS is down, the entire pipeline fails (no fallback LLM)
- Matches the user's existing `LLMService` pattern for consistency

## Implementation Notes
- Client initialization happens once (singleton pattern)
- Handle None content with reasoning_content fallback (matching existing pattern)
- Strip any markdown artifacts from LLM response before returning
- Log the generated post at info level for debugging
- Prompt templates are separate from logic for easy iteration

## References
- SPEC-005
