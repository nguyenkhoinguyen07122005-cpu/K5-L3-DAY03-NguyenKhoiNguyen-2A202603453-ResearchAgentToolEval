---
name: wikipedia
track: bonus
kind: live_api
provider: Wikipedia REST API (no key)
requires_env: []
inputs: [query, lang, limit]
outputs: [items]
side_effect: false
---
# wikipedia

Searches Wikipedia (`/w/rest.php/v1/search/page`) and enriches the best match
with its lead summary (`/api/rest_v1/page/summary/{title}`).

- Use for **background / encyclopedic** questions: who someone is, what a concept,
  organisation or model architecture is, history of something.
- Do **not** use for news (`lookup`), tweets (`timeline`/`social_search`) or papers (`papers`).
- `lang`: Wikipedia language code (`en`, `vi`, ...). Invalid values fall back to `en`.
- `limit` is clamped to 1–10. Empty `query` returns an error dict without calling the network.
- No API key; sends a descriptive `User-Agent` as required by Wikimedia.
