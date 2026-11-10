from __future__ import annotations

import re
from typing import Any

import requests

from tools._shared import TIMEOUT, clamp_int, err


HF_MODELS_URL = "https://huggingface.co/api/models"
SORT_FIELDS = {"downloads": "downloads", "likes": "likes", "trending": "trendingScore", "recent": "createdAt"}


def hf_model_search(query: str = "", task: str = "", sort: str = "downloads", limit: int = 5) -> dict[str, Any]:
    """Search models on the Hugging Face Hub (public API, no key)."""
    query = (query or "").strip()
    task = re.sub(r"[^a-z0-9\-]", "", str(task or "").strip().lower().replace(" ", "-"))
    if not query and not task:
        return {"tool": "hf_model_search", "error": "ValueError", "message": "query or task is required"}
    try:
        sort = str(sort or "downloads").strip().lower()
        sort = sort if sort in SORT_FIELDS else "downloads"
        limit = clamp_int(limit, 5, 1, 20)
        params: dict[str, Any] = {"sort": SORT_FIELDS[sort], "direction": -1, "limit": limit}
        if query:
            params["search"] = query
        if task:
            params["pipeline_tag"] = task

        response = requests.get(HF_MODELS_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        models = data if isinstance(data, list) else []
        items: list[dict[str, Any]] = []
        for model in models:
            model_id = model.get("id") or model.get("modelId")
            if not model_id:
                continue
            items.append({
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "source": "huggingface.co",
                "summary": f"task={model.get('pipeline_tag') or 'n/a'}; downloads={model.get('downloads')}; likes={model.get('likes')}",
                "task": model.get("pipeline_tag"),
                "date": model.get("lastModified") or model.get("createdAt"),
                "metrics": {"downloads": model.get("downloads"), "likes": model.get("likes")},
            })
        return {"tool": "hf_model_search", "query": query, "task": task or None, "sort": sort, "items": items[:limit]}
    except Exception as exc:
        return err("hf_model_search", exc)
