from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, clamp_int, err


USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"
_TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str | None) -> str:
    return " ".join(_TAG_RE.sub("", text or "").split())


def _lang(value: Any) -> str:
    lang = str(value or "en").strip().lower()
    return lang if re.fullmatch(r"[a-z]{2,3}", lang) else "en"


def wiki_search(query: str = "", lang: str = "en", limit: int = 3) -> dict[str, Any]:
    """Search Wikipedia and return the top pages plus the full lead summary of the best match."""
    query = (query or "").strip()
    lang = _lang(lang)
    if not query:
        return {"tool": "wiki_search", "error": "ValueError", "message": "query must not be empty"}
    try:
        limit = clamp_int(limit, 3, 1, 10)
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(
            f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page",
            params={"q": query, "limit": limit},
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        pages = response.json().get("pages") or []
        items: list[dict[str, Any]] = []
        for page in pages[:limit]:
            key = page.get("key") or (page.get("title") or "").replace(" ", "_")
            if not key:
                continue
            description = _clean(page.get("description"))
            excerpt = _clean(page.get("excerpt"))
            items.append({
                "title": page.get("title") or key.replace("_", " "),
                "url": f"https://{lang}.wikipedia.org/wiki/{quote(key)}",
                "source": f"{lang}.wikipedia.org",
                "description": description,
                "summary": " — ".join(part for part in (description, excerpt) if part),
            })

        # Enrich the best match with the page's lead section (best-effort; search results stay usable).
        if items:
            try:
                key = items[0]["url"].rsplit("/", 1)[-1]
                summary_resp = requests.get(
                    f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{key}",
                    headers=headers,
                    timeout=TIMEOUT,
                )
                summary_resp.raise_for_status()
                extract = (summary_resp.json() or {}).get("extract")
                if extract:
                    items[0]["summary"] = extract[:3000]
            except Exception:
                pass

        return {"tool": "wiki_search", "query": query, "lang": lang, "items": items}
    except Exception as exc:
        return err("wiki_search", exc)
