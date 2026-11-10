from __future__ import annotations

import time
from typing import Any

import requests

from tools._shared import TIMEOUT, clamp_int, domain, err


HN_API = "https://hn.algolia.com/api/v1"
TIMEFRAME_SECONDS = {"day": 86_400, "week": 7 * 86_400, "month": 30 * 86_400, "year": 365 * 86_400}


def hn_search(query: str = "", sort: str = "top", timeframe: str = "all", limit: int = 5) -> dict[str, Any]:
    """Search Hacker News stories via the public Algolia API."""
    query = (query or "").strip()
    if not query:
        return {"tool": "hn_search", "error": "ValueError", "message": "query must not be empty"}
    try:
        sort = str(sort or "top").strip().lower()
        sort = sort if sort in {"top", "latest"} else "top"
        timeframe = str(timeframe or "all").strip().lower()
        timeframe = timeframe if timeframe in TIMEFRAME_SECONDS else "all"
        limit = clamp_int(limit, 5, 1, 30)

        endpoint = f"{HN_API}/search" if sort == "top" else f"{HN_API}/search_by_date"
        params: dict[str, Any] = {"query": query, "tags": "story", "hitsPerPage": limit}
        if timeframe != "all":
            params["numericFilters"] = f"created_at_i>{int(time.time()) - TIMEFRAME_SECONDS[timeframe]}"

        response = requests.get(endpoint, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        hits = response.json().get("hits") or []
        items: list[dict[str, Any]] = []
        for hit in hits:
            story_id = hit.get("objectID")
            if not story_id:
                continue
            discussion = f"https://news.ycombinator.com/item?id={story_id}"
            link = hit.get("url") or discussion
            items.append({
                "title": hit.get("title") or hit.get("story_title") or "",
                "url": link,
                "discussion_url": discussion,
                "source": domain(link) if hit.get("url") else "news.ycombinator.com",
                "summary": (hit.get("story_text") or hit.get("title") or "")[:500],
                "date": hit.get("created_at"),
                "metrics": {"points": hit.get("points"), "comments": hit.get("num_comments")},
                "author": hit.get("author"),
            })
        return {"tool": "hn_search", "query": query, "sort": sort, "timeframe": timeframe, "items": items[:limit]}
    except Exception as exc:
        return err("hn_search", exc)
