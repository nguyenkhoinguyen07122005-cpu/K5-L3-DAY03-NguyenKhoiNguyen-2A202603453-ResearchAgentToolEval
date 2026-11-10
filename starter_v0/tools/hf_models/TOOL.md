---
name: hf_models
track: bonus
kind: live_api
provider: Hugging Face Hub API (no key)
requires_env: []
inputs: [query, task, sort, limit]
outputs: [items]
side_effect: false
---
# hf_models

Searches models on the Hugging Face Hub via `https://huggingface.co/api/models`.

- `task` is a Hub pipeline tag (`text-generation`, `text-to-image`, `automatic-speech-recognition`, ...) → `pipeline_tag`.
- `sort`: `downloads` (default, "tải nhiều nhất"), `likes`, `trending`, `recent` → mapped to Hub sort fields.
- Use for **finding open models / checkpoints** on Hugging Face. Papers → `papers`, code repos → `github_repos`.
- Needs at least `query` or `task`; otherwise returns an error dict without calling the network.
- `limit` clamped to 1–20; unknown `sort` falls back to `downloads`.
