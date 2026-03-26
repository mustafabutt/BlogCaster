"""
Record Keeper MCP Server

FastMCP server that manages a JSON-based record of published blog posts.
Provides four tools:
  - is_published: Check if a blog URL has already been posted
  - save_record: Save a new posting record
  - get_records: Return all records
  - get_records_by_platform: Return records filtered by platform

All state is stored in content/records/published_record.json.
"""

import json
import logging
import os
import shutil
import tempfile
from urllib.parse import urlparse, urlunparse

import aiofiles
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("record-keeper")
logger.setLevel(logging.WARNING)

mcp = FastMCP("record-keeper")

RECORDS_PATH = os.environ.get("RECORDS_PATH", "content/records/published_record.json")


def normalize_url(url: str) -> str:
    """Normalize a blog URL for consistent duplicate checking.

    Strips trailing slashes, removes query parameters and fragments,
    and lowercases the URL.
    """
    parsed = urlparse(url.strip())
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/").lower(),
        "",  # params
        "",  # query
        "",  # fragment
    ))
    return normalized


async def read_records() -> dict:
    """Read the records file. Creates it if it doesn't exist.
    Handles corrupted JSON by backing up and starting fresh.
    """
    if not os.path.exists(RECORDS_PATH):
        os.makedirs(os.path.dirname(RECORDS_PATH), exist_ok=True)
        await write_records_atomic({"records": []})
        return {"records": []}

    try:
        async with aiofiles.open(RECORDS_PATH, "r") as f:
            content = await f.read()
        if not content.strip():
            return {"records": []}
        data = json.loads(content)
        if "records" not in data:
            data["records"] = []
        return data
    except json.JSONDecodeError:
        logger.error(f"Corrupted JSON in {RECORDS_PATH}, backing up and starting fresh")
        backup_path = RECORDS_PATH + ".corrupted.bak"
        shutil.copy2(RECORDS_PATH, backup_path)
        logger.info(f"Backup saved to {backup_path}")
        fresh = {"records": []}
        await write_records_atomic(fresh)
        return fresh


async def write_records_atomic(data: dict) -> None:
    """Write records to file atomically using temp file + rename."""
    os.makedirs(os.path.dirname(RECORDS_PATH), exist_ok=True)
    dir_name = os.path.dirname(RECORDS_PATH)

    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        async with aiofiles.open(fd, "w", closefd=True) as f:
            await f.write(json.dumps(data, indent=2))
        os.replace(tmp_path, RECORDS_PATH)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


@mcp.tool()
async def is_published(blog_url: str) -> bool:
    """Check if a blog URL has already been posted.

    Args:
        blog_url: The blog post URL to check

    Returns:
        True if the URL is already in the published record, False otherwise.
    """
    normalized = normalize_url(blog_url)
    logger.info(f"Checking if published: {normalized}")

    try:
        data = await read_records()
        for record in data["records"]:
            if normalize_url(record["blog_url"]) == normalized:
                logger.info(f"Already published: {normalized}")
                return True
        logger.info(f"Not published yet: {normalized}")
        return False
    except Exception as e:
        logger.error(f"Error checking published status: {e}")
        return False


@mcp.tool()
async def save_record(blog_url: str, title: str, platform_id: str, results: dict) -> bool:
    """Save a new posting record to the JSON file.

    Args:
        blog_url: The blog post URL that was shared
        title: The blog post title
        platform_id: The platform ID (e.g. "aspose", "groupdocs")
        results: Per-platform posting outcomes (e.g. {"linkedin": {"status": "success", "post_id": "xxx", "shared_at": "..."}})

    Returns:
        True on success, False on failure.
    """
    normalized = normalize_url(blog_url)
    logger.info(f"Saving record for: {normalized}")

    try:
        data = await read_records()

        # Check if URL already exists to prevent duplicates
        for record in data["records"]:
            if normalize_url(record["blog_url"]) == normalized:
                logger.warning(f"Record already exists for: {normalized}, updating shared_on")
                record["shared_on"].update(results)
                await write_records_atomic(data)
                return True

        new_record = {
            "blog_url": normalized,
            "title": title,
            "platform_id": platform_id,
            "shared_on": results,
        }
        data["records"].append(new_record)
        await write_records_atomic(data)
        logger.info(f"Record saved for: {normalized}")
        return True
    except Exception as e:
        logger.error(f"Error saving record: {e}")
        return False


@mcp.tool()
async def get_records() -> list:
    """Return all records from the published record file.

    Returns:
        List of all published records. Empty list if no records exist.
    """
    logger.info("Fetching all records")
    try:
        data = await read_records()
        return data["records"]
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        return []


@mcp.tool()
async def get_records_by_platform(platform_id: str) -> list:
    """Return records filtered by platform ID.

    Args:
        platform_id: The platform ID to filter by (e.g. "aspose")

    Returns:
        List of records matching the platform. Empty list if none match.
    """
    logger.info(f"Fetching records for platform: {platform_id}")
    try:
        data = await read_records()
        filtered = [r for r in data["records"] if r.get("platform_id") == platform_id]
        logger.info(f"Found {len(filtered)} records for platform: {platform_id}")
        return filtered
    except Exception as e:
        logger.error(f"Error fetching records by platform: {e}")
        return []


if __name__ == "__main__":
    mcp.run(transport="stdio")
