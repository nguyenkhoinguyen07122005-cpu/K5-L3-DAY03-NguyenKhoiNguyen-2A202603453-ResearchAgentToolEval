---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News Algolia API (no key)
requires_env: []
inputs: [query, sort, timeframe, limit]
outputs: [items]
side_effect: false
---
# hackernews

Searches Hacker News stories through `https://hn.algolia.com/api/v1`.

- `sort="top"` → `/search` (relevance + points); `sort="latest"` → `/search_by_date`.
- `timeframe` in `day|week|month|year` adds `numericFilters=created_at_i>…`; `all` (default) adds no filter.
- Each item keeps both the article `url` and the HN `discussion_url`, plus points/comments.
- Use only when the user asks about **Hacker News / HN / dân dev trên HN**. Twitter → `social_search`, web news → `lookup`.
- Out-of-enum `sort`/`timeframe` fall back to defaults; `limit` is clamped to 1–30; empty `query` → error dict, no request.
