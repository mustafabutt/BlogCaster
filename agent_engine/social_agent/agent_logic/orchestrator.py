"""
Orchestrator

Core workflow engine for both Manual and Auto modes.
Coordinates MCP servers and LLM formatter to execute the full pipeline.
"""

import logging
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from agent_engine.social_agent.config import settings
from agent_engine.social_agent.tools.mcp_tools import (
    MCPSessions,
    linkedin_post,
    linkedin_validate_token,
    record_get_all,
    record_is_published,
    record_save,
    rss_fetch_post_by_url,
    rss_get_latest_posts,
)
from agent_engine.social_agent.utils.helpers import (
    detect_platform_from_url,
    find_platform_by_id,
    get_active_platforms,
    load_registry,
)
from agent_engine.social_agent.utils.llm_service import format_for_linkedin

logger = logging.getLogger("social_agent")


def _normalize_url(url: str) -> str:
    """Normalize a URL for comparison (same logic as record-keeper)."""
    parsed = urlparse(url.strip())
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/").lower(),
        "", "", "",
    ))


async def run_manual_mode(sessions: MCPSessions, url: str) -> bool:
    """Execute Manual Mode: post a specific blog URL to LinkedIn.

    Steps:
        1. Auto-detect platform from URL
        2. Check if already published
        3. Fetch post content by URL
        4. Format via LLM
        5. Validate LinkedIn token
        6. Post to LinkedIn
        7. Save record

    Args:
        sessions: Active MCP server sessions
        url: The blog post URL to share

    Returns:
        True if posted successfully, False otherwise
    """
    logger.info(f"Starting Manual Mode for URL: {url}")

    # 1. Load registry and detect platform
    registry_path = settings.resolve_path(settings.REGISTRY_PATH)
    registry = load_registry(registry_path)
    platform = detect_platform_from_url(registry, url)

    if platform:
        platform_id = platform["id"]
        logger.info(f"Platform detected: {platform_id}")
    else:
        platform_id = "unknown"
        logger.warning(f"URL does not match any registered platform, using platform_id='unknown'")

    # 2. Check if already published
    logger.info("Checking if URL is already published...")
    already_published = await record_is_published(sessions, url)
    if already_published:
        logger.info(f"Already published: {url} — skipping")
        print(f"This URL has already been posted: {url}")
        return False

    logger.info("Record check: not published yet")

    # 3. Fetch post content
    logger.info("Fetching post content...")
    post_data = await rss_fetch_post_by_url(sessions, url)

    if post_data.get("status") == "failed":
        logger.error(f"Failed to fetch post: {post_data.get('error')}")
        print(f"Error fetching post: {post_data.get('error')}")
        return False

    title = post_data.get("title", "Unknown")
    content = post_data.get("content", "")
    logger.info(f"Fetched post: \"{title}\" ({len(content)} chars)")

    # 4. Format via LLM
    logger.info("Formatting post via LLM...")
    try:
        formatted_post = await format_for_linkedin(title, content, url)
    except Exception as e:
        logger.error(f"LLM formatting failed: {e}")
        print(f"Error formatting post: {e}")
        return False

    if not formatted_post:
        logger.error("LLM returned empty formatted post")
        print("Error: LLM returned empty content")
        return False

    # 5. Validate LinkedIn token
    logger.info("Validating LinkedIn token...")
    token_valid = await linkedin_validate_token(sessions)
    if not token_valid:
        logger.error("LinkedIn token is invalid or expired")
        print("Error: LinkedIn access token is invalid or expired. Please refresh it.")
        return False

    logger.info("LinkedIn token is valid")

    # 6. Post to LinkedIn
    logger.info("Posting to LinkedIn...")
    linkedin_result = await linkedin_post(sessions, formatted_post, url)

    if linkedin_result.get("status") != "success":
        logger.error(f"LinkedIn posting failed: {linkedin_result.get('error')}")
        print(f"Error posting to LinkedIn: {linkedin_result.get('error')}")
        # Still save the failure record
        await _save_record(sessions, url, title, platform_id, linkedin_result)
        return False

    post_id = linkedin_result.get("post_id", "")
    logger.info(f"LinkedIn post successful: post_id={post_id}")
    print(f"Successfully posted to LinkedIn! Post ID: {post_id}")

    # 7. Save record
    await _save_record(sessions, url, title, platform_id, linkedin_result)

    logger.info(f"Manual Mode complete for: {url}")
    return True


async def run_auto_mode(sessions: MCPSessions, platform_id: str) -> bool:
    """Execute Auto Mode: find and post the latest unpublished blog for a platform.

    Fetches ALL posts from the RSS feed and ALL published records, then
    does in-memory matching to find the first unpublished post. This means
    the agent will always find the next unposted blog — new posts first,
    then traversing backwards through older ones.

    Steps:
        1. Load registry and validate platform
        2. Fetch all posts from RSS feed
        3. Load all published records and build lookup set
        4. Find first unpublished post (newest first)
        5. Format via LLM
        6. Validate LinkedIn token
        7. Post to LinkedIn
        8. Save record

    Args:
        sessions: Active MCP server sessions
        platform_id: The platform ID from the registry

    Returns:
        True if posted successfully, False otherwise
    """
    logger.info(f"Starting Auto Mode for platform: {platform_id}")

    # 1. Load registry and validate platform
    registry_path = settings.resolve_path(settings.REGISTRY_PATH)
    registry = load_registry(registry_path)
    platform = find_platform_by_id(registry, platform_id)

    if not platform:
        available = [p["id"] for p in get_active_platforms(registry)]
        logger.error(f"Platform '{platform_id}' not found in registry")
        print(f"Error: Platform '{platform_id}' not found.")
        print(f"Available platforms: {', '.join(available)}")
        return False

    if not platform.get("active", False):
        logger.warning(f"Platform '{platform_id}' is inactive")
        print(f"Error: Platform '{platform_id}' is inactive.")
        return False

    rss_url = platform["rss_feed"]
    logger.info(f"Platform '{platform_id}' found: {platform['name']} (RSS: {rss_url})")

    # 2. Fetch ALL posts from RSS feed (limit=0 means no limit)
    logger.info("Fetching all posts from RSS feed...")
    posts = await rss_get_latest_posts(sessions, rss_url, limit=0)

    if not posts:
        logger.warning("No posts found in RSS feed")
        print(f"No posts found in the RSS feed for {platform['name']}.")
        return False

    logger.info(f"Fetched {len(posts)} posts from RSS feed")

    # 3. Load all published records and build a set of normalized URLs
    logger.info("Loading published records...")
    records = await record_get_all(sessions)
    published_urls = {_normalize_url(r["blog_url"]) for r in records if r.get("blog_url")}
    logger.info(f"Found {len(published_urls)} published records")

    # 4. Find first unpublished post with a valid URL (newest first)
    unpublished_post = None
    skipped_published = 0
    skipped_broken = 0
    for post in posts:
        post_url = post.get("link", "")
        if not post_url:
            continue
        if _normalize_url(post_url) in published_urls:
            skipped_published += 1
            continue

        # Validate URL points to a real blog post (not a listing/404 page)
        logger.info(f"Validating candidate URL: {post_url}")
        post_data = await rss_fetch_post_by_url(sessions, post_url)

        if post_data.get("status") == "failed":
            logger.warning(f"Skipping unreachable URL: {post_url} — {post_data.get('error')}")
            skipped_broken += 1
            continue

        fetched_title = post_data.get("title", "")
        fetched_content = post_data.get("content", "")

        # A real blog post should have a proper title (not "Unknown") and
        # substantial content (at least 200 chars). Generic listing pages
        # and soft-404s fail these checks.
        if not fetched_title or fetched_title == "Unknown" or len(fetched_content) < 200:
            logger.warning(
                f"Skipping invalid page: {post_url} "
                f"(title='{fetched_title[:50]}', content_len={len(fetched_content)})"
            )
            skipped_broken += 1
            continue

        unpublished_post = post
        unpublished_post["_fetched_content"] = fetched_content
        unpublished_post["_fetched_title"] = fetched_title
        break

    if not unpublished_post:
        logger.warning(f"No valid unpublished posts found (published: {skipped_published}, broken: {skipped_broken})")
        print(f"No valid unpublished posts found from {platform['name']}.")
        return False

    post_url = unpublished_post["link"]
    title = unpublished_post.get("_fetched_title") or unpublished_post.get("title", "Unknown")
    summary = unpublished_post.get("summary", "")
    fetched_content = unpublished_post.get("_fetched_content", "")
    logger.info(f"Skipped {skipped_published} already-published, {skipped_broken} broken URLs")
    logger.info(f"Selected unpublished post: \"{title}\" — {post_url}")

    # 5. Format via LLM (prefer fetched page content over RSS summary)
    content_for_llm = fetched_content if fetched_content else summary
    logger.info("Formatting post via LLM...")
    try:
        formatted_post = await format_for_linkedin(title, content_for_llm, post_url)
    except Exception as e:
        logger.error(f"LLM formatting failed: {e}")
        print(f"Error formatting post: {e}")
        return False

    if not formatted_post:
        logger.error("LLM returned empty formatted post")
        print("Error: LLM returned empty content")
        return False

    # 6. Validate LinkedIn token
    logger.info("Validating LinkedIn token...")
    token_valid = await linkedin_validate_token(sessions)
    if not token_valid:
        logger.error("LinkedIn token is invalid or expired")
        print("Error: LinkedIn access token is invalid or expired. Please refresh it.")
        return False

    logger.info("LinkedIn token is valid")

    # 7. Post to LinkedIn
    logger.info("Posting to LinkedIn...")
    linkedin_result = await linkedin_post(sessions, formatted_post, post_url)

    if linkedin_result.get("status") != "success":
        logger.error(f"LinkedIn posting failed: {linkedin_result.get('error')}")
        print(f"Error posting to LinkedIn: {linkedin_result.get('error')}")
        await _save_record(sessions, post_url, title, platform_id, linkedin_result)
        return False

    post_id = linkedin_result.get("post_id", "")
    logger.info(f"LinkedIn post successful: post_id={post_id}")
    print(f"Successfully posted to LinkedIn! Post ID: {post_id}")

    # 8. Save record
    await _save_record(sessions, post_url, title, platform_id, linkedin_result)

    logger.info(f"Auto Mode complete for platform: {platform_id}")
    return True


async def _save_record(sessions: MCPSessions, blog_url: str, title: str, platform_id: str, linkedin_result: dict) -> None:
    """Save a posting record with LinkedIn results.

    Args:
        sessions: Active MCP server sessions
        blog_url: Blog post URL
        title: Blog post title
        platform_id: Platform ID
        linkedin_result: Result dict from LinkedIn posting
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = {
        "linkedin": {
            "status": linkedin_result.get("status", "failure"),
            "post_id": linkedin_result.get("post_id", ""),
            "shared_at": timestamp,
        }
    }

    saved = await record_save(sessions, blog_url, title, platform_id, results)
    if saved:
        logger.info(f"Record saved for {blog_url}")
    else:
        logger.error(f"Failed to save record for {blog_url}")
