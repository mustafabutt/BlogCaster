# SPEC-005: LLM Formatter Service

## Title
LLM Formatter — Formats blog content into LinkedIn posts using GPT-OSS

## Description
A service module that takes blog post data (title, summary, URL) and generates a professional LinkedIn post using the company's self-hosted GPT-OSS LLM via the OpenAI Python SDK. The formatter uses a structured prompt to produce consistent, engaging posts.

## Functions

### `format_for_linkedin(title: str, summary: str, blog_url: str) -> str`
- Takes blog post data and generates a formatted LinkedIn post
- Uses AsyncOpenAI client pointed at GPT-OSS endpoint
- Returns the formatted post text ready to publish

## LinkedIn Post Requirements
- Professional tone
- 150-200 words
- Start with a hook line that grabs attention
- 3-5 relevant hashtags at the end
- Blog URL included at the end
- No emojis unless part of the blog content

## LLM Configuration
- Client: `AsyncOpenAI(base_url=PROFESSIONALIZE_BASE_URL, api_key=PROFESSIONALIZE_API_KEY_2)`
- Model: `PROFESSIONALIZE_LLM_MODEL`
- Temperature: 0.7 (creative but controlled)
- Max tokens: 1000

## Acceptance Criteria
- [ ] Uses OpenAI Python SDK with AsyncOpenAI client
- [ ] Reads LLM config from environment variables via Pydantic settings
- [ ] Generates posts matching the LinkedIn format requirements
- [ ] Handles LLM API errors gracefully (timeout, empty response)
- [ ] Returns clean text with no markdown artifacts
- [ ] Prompt is defined in `utils/prompts.py`, not hardcoded in function

## Dependencies
- `PROFESSIONALIZE_BASE_URL`, `PROFESSIONALIZE_API_KEY_2`, `PROFESSIONALIZE_LLM_MODEL` env vars

## Edge Cases
- LLM returns empty response
- LLM returns response with markdown formatting (strip it)
- Blog summary is very short or empty (use title-only prompt)
- LLM API timeout
- LLM returns content exceeding LinkedIn character limit

## Out of Scope
- Multi-turn LLM conversations
- Agent-based LLM workflows
- Image generation for posts
- Post in languages other than English
