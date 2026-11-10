from __future__ import annotations

import os
import re
from datetime import date, timedelta
from typing import Any

import requests

from tools._shared import TIMEOUT, clamp_int, err


GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
CREATED_WITHIN_DAYS = {"week": 7, "month": 30, "year": 365}


def github_search(query: str = "", language: str = "", sort: str = "stars", created_within: str = "any", limit: int = 5) -> dict[str, Any]:
    """Search public GitHub repositories (GitHub REST search API)."""
    query = (query or "").strip()
    if not query:
        return {"tool": "github_search", "error": "ValueError", "message": "query must not be empty"}
    try:
        sort = str(sort or "stars").strip().lower()
        sort = sort if sort in {"stars", "updated", "best_match"} else "stars"
        created_within = str(created_within or "any").strip().lower()
        limit = clamp_int(limit, 5, 1, 20)

        qualifiers = [query]
        language = re.sub(r"[^A-Za-z0-9+#.\- ]", "", str(language or "")).strip()
        if language:
            qualifiers.append(f'language:"{language}"' if " " in language else f"language:{language}")
        if created_within in CREATED_WITHIN_DAYS:
            since = date.today() - timedelta(days=CREATED_WITHIN_DAYS[created_within])
            qualifiers.append(f"created:>{since.isoformat()}")

        params: dict[str, Any] = {"q": " ".join(qualifiers), "per_page": limit}
        if sort != "best_match":
            params.update({"sort": sort, "order": "desc"})
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "AI20k-Day03-Research-Agent"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(GITHUB_SEARCH_URL, params=params, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        items = [{
            "title": repo.get("full_name"),
            "url": repo.get("html_url"),
            "source": "github.com",
            "summary": (repo.get("description") or "")[:500],
            "language": repo.get("language"),
            "date": repo.get("pushed_at") or repo.get("updated_at"),
            "metrics": {"stars": repo.get("stargazers_count"), "forks": repo.get("forks_count")},
        } for repo in data.get("items") or [] if repo.get("full_name")]
        return {
            "tool": "github_search",
            "query": query,
            "api_query": params["q"],
            "sort": sort,
            "total_count": data.get("total_count"),
            "items": items[:limit],
        }
    except Exception as exc:
        return err("github_search", exc)
