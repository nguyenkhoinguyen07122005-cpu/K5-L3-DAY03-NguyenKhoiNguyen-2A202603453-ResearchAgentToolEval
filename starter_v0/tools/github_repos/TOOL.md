---
name: github_repos
track: bonus
kind: live_api
provider: GitHub REST API (search/repositories)
requires_env: []
optional_env: [GITHUB_TOKEN]
inputs: [query, language, sort, created_within, limit]
outputs: [items, total_count]
side_effect: false
---
# github_repos

Searches public GitHub repositories. Works without a key (≈10 requests/min);
set `GITHUB_TOKEN` in `.env` for a higher rate limit. The token is only sent in
the `Authorization` header, never returned in the result.

- `language` → `language:<lang>` qualifier; `created_within` (`week|month|year`) → `created:>YYYY-MM-DD`.
- `sort`: `stars` (default, "nhiều sao nhất"), `updated` (mới cập nhật), `best_match`.
- Use to **find** open-source repos/projects/libraries. Do **not** use to write code (out of scope).
- Out-of-enum values fall back to defaults; `limit` clamped to 1–20; empty `query` → error dict, no request.
