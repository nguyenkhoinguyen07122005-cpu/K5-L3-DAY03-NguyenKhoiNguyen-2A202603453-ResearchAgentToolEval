"""Tool Unit Test Challenge — completed.

Sections:
1. Former TODO stubs for the starter tools (clarify, format, send, lookup, fetch, timeline,
   social_search, policy).
2. Tests for the 4 team-added tools (appended at the end of this file by the new-tools package).
3. Regression tests for bugs found in the starter tools (see REPORT.md B5). Each one FAILED on
   the original starter code and passes after the fix.

Rules: offline only (`fake_http`), one behaviour per test, assert both the request we send and
the result we return.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send = TOOL_FUNCTIONS["send"]
lookup = TOOL_FUNCTIONS["lookup"]
fetch = TOOL_FUNCTIONS["fetch"]
timeline = TOOL_FUNCTIONS["timeline"]
social_search = TOOL_FUNCTIONS["social_search"]
policy = TOOL_FUNCTIONS["policy"]


def _tweets(n: int, handle: str = "sama", start: int = 1) -> list[dict]:
    return [{"tweet_id": str(start + i), "screen_name": handle, "text": f"tweet {start + i}\nbody"} for i in range(n)]


@pytest.fixture
def twitter_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk-test")
    monkeypatch.setenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")


@pytest.fixture
def telegram_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:SECRET-TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100777")


# =====================================================================
# 1. Starter tools (former TODO stubs)
# =====================================================================

# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify(question="Bạn muốn nguồn nào?", response_type="choice", options=["web", "twitter"])

    assert result["options"] == ["web", "twitter"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections", headline="Digest")["markdown"]

    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("a2") < markdown.index("## B")  # a2 grouped under A, not after B


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"t{i}", "url": f"https://x.com/{i}"} for i in range(3)]
    markdown = format_tool(items=items, template="thread")["markdown"]

    lines = [line for line in markdown.split("\n") if line.strip()]
    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    for empty in (None, []):
        result = format_tool(items=empty, template="sections")
        assert result["item_count"] == 0
        assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(telegram_env, fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "123456:SECRET-TOKEN" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100777"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send(text="Bản tin", confirmed=True)

    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tv-test")
    calls = fake_http(FakeResponse({"results": []}))
    result = lookup(query="AI", topic="general", timeframe=None)

    assert "time_range" not in calls[0]["json"]
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nBody",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/post"},
    }}))
    result = fetch(url="https://www.example.com/post")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"]["url"] == "https://www.example.com/post"
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-test"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.example.com/post", "source": "example.com", "summary": "# Hello\nBody",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({"data": {"markdown": "y" * 9000, "metadata": {}}}))
    item = fetch(url="https://example.com")["items"][0]

    assert len(item["summary"]) == 4000
    assert item["title"] == "https://example.com"  # falls back to the URL when there is no title


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(twitter_env, fake_http) -> None:
    raw = [{"screen_name": "sama", "text": "no id"}] + _tweets(6)
    calls = fake_http(FakeResponse({"timeline": raw}))
    result = timeline(screenname="sama", limit=3)

    assert calls[0]["url"] == "https://twitter-api45.p.rapidapi.com/timeline.php"
    assert calls[0]["params"] == {"screenname": "sama"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "rk-test"
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [f"https://x.com/sama/status/{i}" for i in (1, 2, 3)]


def test_social_search_passes_search_type(twitter_env, fake_http) -> None:
    for search_type in ("Top", "Latest"):
        calls = fake_http(FakeResponse({"timeline": _tweets(2, "openai")}))
        result = social_search(query="OpenAI", search_type=search_type)

        assert calls[0]["url"].endswith("/search.php")
        assert calls[0]["params"] == {"query": "OpenAI", "search_type": search_type}
        assert result["search_type"] == search_type
        assert len(result["items"]) == 2


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    for empty in ("", "   ", "?!"):
        assert policy(query=empty)["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy(query="API key dữ liệu khách hàng prompt", policy_area="data_privacy", top_k=5)

    assert result["results"], "expected at least one data_privacy section"
    assert {hit["policy_area"] for hit in result["results"]} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy(query="viral tweet verified fact citation", policy_area="source_citation", top_k=10)

    flagged = [hit for hit in result["results"] if any("viral tweet" in line for line in hit["untrusted_text"])]
    assert flagged, "the quoted instruction-like line must be returned as untrusted_text"
    for hit in flagged:
        assert "Assistant:" not in hit["facts"]
        assert not any(line in hit["facts"] for line in hit["untrusted_text"])


# =====================================================================
# 3. Regression tests: bugs found in starter tools (all failed before the fix)
# =====================================================================

def test_send_string_false_is_not_treated_as_confirmation(telegram_env, fake_http) -> None:
    """BUG-1: model sent confirmed="false" (a non-empty string -> truthy) and the message WAS posted."""
    calls = fake_http(FakeResponse({"ok": True}))
    for value in ("false", "False", "no", 0, None, "yes please?"):
        result = send(text="Bản tin", confirmed=value)
        assert result["status"] == "needs_confirmation", value
    assert calls == []


def test_send_needs_confirmation_pauses_chat_loop(fake_http) -> None:
    """BUG-1b: needs_confirmation was not flagged awaiting_user, so chat.py kept looping."""
    fake_http(FakeResponse({"ok": True}))
    result = send(text="Bản tin", confirmed=False)
    assert result["awaiting_user"] is True
    assert "Bản tin" in result["question"]


def test_send_error_message_does_not_leak_bot_token(telegram_env, monkeypatch) -> None:
    """BUG-2: requests' HTTPError text contains the full URL -> bot token ended up in transcripts."""
    import requests

    class LeakyResponse(FakeResponse):
        def raise_for_status(self) -> None:
            raise requests.HTTPError("401 Client Error: Unauthorized for url: https://api.telegram.org/bot123456:SECRET-TOKEN/sendMessage")

    monkeypatch.setattr(requests, "post", lambda url, **kw: LeakyResponse(status_code=401))
    result = send(text="x", confirmed=True)
    assert result["error"] == "HTTPError"
    assert "SECRET-TOKEN" not in str(result)


def test_send_retries_without_markdown_when_telegram_rejects_entities(telegram_env, monkeypatch) -> None:
    """BUG-3: digest text with unbalanced '*'/'_' -> Telegram 400 'can't parse entities' -> nothing sent."""
    import requests

    posted: list[dict] = []

    def fake_post(url, **kwargs):
        posted.append(kwargs["json"])
        return FakeResponse(status_code=400 if "parse_mode" in kwargs["json"] else 200)

    monkeypatch.setattr(requests, "post", fake_post)
    result = send(text="**AI_news* digest", confirmed=True)
    assert result["status"] == "sent"
    assert [("parse_mode" in body) for body in posted] == [True, False]


def test_timeline_strips_at_sign_from_handle(twitter_env, fake_http) -> None:
    """BUG-4: model passed '@sama' -> API looked up a non-existent account '@sama'."""
    calls = fake_http(FakeResponse({"timeline": _tweets(1)}))
    result = timeline(screenname=" @sama ")
    assert calls[0]["params"] == {"screenname": "sama"}
    assert result["screenname"] == "sama"


def test_timeline_limit_edge_values(twitter_env, fake_http) -> None:
    """BUG-5: limit=-1 silently dropped the LAST tweet (items[:-1]); limit=0 returned 5."""
    fake_http(FakeResponse({"timeline": _tweets(6)}))
    assert len(timeline(screenname="sama", limit=-1)["items"]) == 1
    assert len(timeline(screenname="sama", limit=0)["items"]) == 1
    assert len(timeline(screenname="sama", limit="4")["items"]) == 4
    assert len(timeline(screenname="sama", limit="abc")["items"]) == 5


def test_social_search_normalises_search_type_case(twitter_env, fake_http) -> None:
    """BUG-6: model sent search_type='top' (lowercase) -> API expects 'Top'."""
    calls = fake_http(FakeResponse({"timeline": []}))
    social_search(query="AI", search_type="top")
    social_search(query="AI", search_type="whatever")
    assert [call["params"]["search_type"] for call in calls] == ["Top", "Latest"]


def test_lookup_clamps_max_results_and_normalises_enums(monkeypatch, fake_http) -> None:
    """BUG-7: max_results=50 / timeframe='today' / topic='News' were forwarded and rejected by Tavily."""
    monkeypatch.setenv("TAVILY_API_KEY", "tv-test")
    calls = fake_http(FakeResponse({"results": []}))
    lookup(query="AI", topic="News", timeframe="today", max_results=50)
    body = calls[0]["json"]
    assert body["max_results"] == 20
    assert body["topic"] == "news"
    assert body["time_range"] == "day"

    lookup(query="AI", topic="sports??", timeframe="someday", max_results="3")
    body = calls[1]["json"]
    assert (body["topic"], body["max_results"]) == ("general", 3)
    assert "time_range" not in body  # unknown timeframe -> no filter rather than an API error


def test_fetch_empty_url_does_not_spend_credit(monkeypatch, fake_http) -> None:
    """BUG-8: fetch(url='') still called Firecrawl (paid credit) and returned a confusing 400."""
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {}}))
    result = fetch(url="  ")
    assert calls == []
    assert result["error"] == "ValueError"


def test_fetch_adds_scheme_to_bare_domain(monkeypatch, fake_http) -> None:
    """BUG-9: 'openai.com/research' (no scheme) was rejected by Firecrawl."""
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {"markdown": "ok", "metadata": {}}}))
    result = fetch(url="openai.com/research")
    assert calls[0]["json"]["url"] == "https://openai.com/research"
    assert result["items"][0]["source"] == "openai.com"


def test_format_accepts_plain_string_items_without_crashing() -> None:
    """BUG-10: model sent items=["headline 1", "headline 2"] -> AttributeError crashed the tool."""
    result = format_tool(items=["headline 1", "headline 2"], template="bullets")
    assert result["item_count"] == 2
    assert result["markdown"] == "- headline 1\n- headline 2"


def test_format_item_without_url_has_no_dangling_separator() -> None:
    """BUG-11: an item without url/source rendered as '- text - ' (dangling dash)."""
    markdown = format_tool(items=[{"title": "No link"}], template="bullets")["markdown"]
    assert markdown == "- No link"


def test_clarify_unknown_response_type_falls_back_to_text() -> None:
    """BUG-12: response_type='free' passed through, UI could not render the question."""
    assert clarify(question="Tài khoản nào?", response_type="free")["response_type"] == "text"
    yes_no = clarify(question="Gửi nhé?", response_type="yes_no")
    assert yes_no["options"] == ["yes", "no"]


# =====================================================================
# 2. Team-added tools (wikipedia, hackernews, github_repos, hf_models) — >= 3 tests per tool
# =====================================================================

wikipedia = TOOL_FUNCTIONS["wikipedia"]
hackernews = TOOL_FUNCTIONS["hackernews"]
github_repos = TOOL_FUNCTIONS["github_repos"]
hf_models = TOOL_FUNCTIONS["hf_models"]


# ---------------- wikipedia ----------------

def test_wikipedia_search_maps_pages_and_enriches_top_summary(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "pages": [
            {"key": "Andrej_Karpathy", "title": "Andrej Karpathy",
             "excerpt": "<span class=\"searchmatch\">Andrej</span> Karpathy is", "description": "AI researcher"},
            {"key": "Karpathy", "title": "Karpathy", "excerpt": "surname", "description": ""},
        ],
        "extract": "Andrej Karpathy is a Slovak-Canadian computer scientist.",
    }))
    result = wikipedia(query="Andrej Karpathy", lang="en", limit=2)

    assert calls[0]["url"] == "https://en.wikipedia.org/w/rest.php/v1/search/page"
    assert calls[0]["params"] == {"q": "Andrej Karpathy", "limit": 2}
    assert "User-Agent" in calls[0]["headers"]
    assert calls[1]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/Andrej_Karpathy"
    assert [item["url"] for item in result["items"]] == [
        "https://en.wikipedia.org/wiki/Andrej_Karpathy", "https://en.wikipedia.org/wiki/Karpathy"]
    assert result["items"][0]["summary"].startswith("Andrej Karpathy is a Slovak")
    assert "<span" not in result["items"][1]["summary"]


def test_wikipedia_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"pages": []}))
    empty = wikipedia(query="   ")
    assert empty["error"] == "ValueError"
    assert calls == []  # empty query never hits the network

    result = wikipedia(query="Transformer", lang="Vietnamese!!", limit="999")
    assert calls[0]["url"].startswith("https://en.wikipedia.org/")  # invalid lang -> en
    assert calls[0]["params"]["limit"] == 10  # string + out of range -> clamped
    assert result["items"] == []


def test_wikipedia_vi_lang_uses_vi_domain(fake_http) -> None:
    calls = fake_http(FakeResponse({"pages": [{"key": "Học_máy", "title": "Học máy"}]}))
    result = wikipedia(query="Học máy", lang="VI")

    assert calls[0]["url"] == "https://vi.wikipedia.org/w/rest.php/v1/search/page"
    assert result["items"][0]["source"] == "vi.wikipedia.org"


def test_wikipedia_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    result = wikipedia(query="Yann LeCun")
    assert result == {"tool": "wiki_search", "error": "HTTPError", "message": "HTTP 503"}


# ---------------- hackernews ----------------

def test_hackernews_top_week_builds_request_and_maps_hits(fake_http, monkeypatch) -> None:
    monkeypatch.setattr("tools.hackernews.tool.time.time", lambda: 1_000_000)
    calls = fake_http(FakeResponse({"hits": [
        {"objectID": "42", "title": "Rust 2.0", "url": "https://blog.rust-lang.org/x", "points": 300,
         "num_comments": 120, "author": "steve", "created_at": "2026-11-01T00:00:00Z"},
        {"objectID": "43", "title": "Ask HN: Rust?", "url": None, "points": 10, "num_comments": 5},
        {"title": "no id"},
    ]}))
    result = hackernews(query="Rust", sort="top", timeframe="week", limit=5)

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "Rust", "tags": "story", "hitsPerPage": 5,
                                  "numericFilters": "created_at_i>395200"}
    assert len(result["items"]) == 2
    first, ask = result["items"]
    assert first["source"] == "blog.rust-lang.org"
    assert first["discussion_url"] == "https://news.ycombinator.com/item?id=42"
    assert first["metrics"] == {"points": 300, "comments": 120}
    assert ask["url"] == "https://news.ycombinator.com/item?id=43"  # Ask HN has no external url


def test_hackernews_latest_uses_search_by_date_and_no_time_filter(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hackernews(query="Claude", sort="latest")

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert "numericFilters" not in calls[0]["params"]


def test_hackernews_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    assert hackernews(query="")["error"] == "ValueError"
    assert calls == []

    result = hackernews(query="AI", sort="Most popular", timeframe="forever", limit="0")
    assert calls[0]["url"].endswith("/search")  # unknown sort -> top
    assert "numericFilters" not in calls[0]["params"]  # unknown timeframe -> all
    assert calls[0]["params"]["hitsPerPage"] == 1  # "0" -> clamped to 1
    assert (result["sort"], result["timeframe"]) == ("top", "all")


def test_hackernews_network_error_returns_error_dict(fake_http) -> None:
    import requests

    fake_http(requests.Timeout("timed out"))
    result = hackernews(query="AI")
    assert result["error"] == "Timeout"


# ---------------- github_repos ----------------

def test_github_repos_builds_qualifiers_and_maps_items(fake_http, monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = fake_http(FakeResponse({"total_count": 1, "items": [
        {"full_name": "qdrant/qdrant", "html_url": "https://github.com/qdrant/qdrant", "description": "Vector DB",
         "language": "Rust", "stargazers_count": 25000, "forks_count": 1500, "pushed_at": "2026-11-09T00:00:00Z"},
        {"html_url": "https://github.com/broken"},
    ]}))
    result = github_repos(query="vector database", language="Rust", sort="stars", limit=5)

    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "vector database language:Rust", "per_page": 5, "sort": "stars", "order": "desc"}
    assert "Authorization" not in calls[0]["headers"]
    assert result["items"] == [{
        "title": "qdrant/qdrant", "url": "https://github.com/qdrant/qdrant", "source": "github.com",
        "summary": "Vector DB", "language": "Rust", "date": "2026-11-09T00:00:00Z",
        "metrics": {"stars": 25000, "forks": 1500},
    }]


def test_github_repos_token_is_sent_but_never_returned(fake_http, monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_SECRET")
    calls = fake_http(FakeResponse({"items": []}))
    result = github_repos(query="agent", created_within="month", sort="best_match")

    assert calls[0]["headers"]["Authorization"] == "Bearer ghp_SECRET"
    assert "created:>" in calls[0]["params"]["q"]
    assert "sort" not in calls[0]["params"]  # best_match = GitHub default ordering
    assert "ghp_SECRET" not in str(result)


def test_github_repos_bad_input_from_model(fake_http, monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = fake_http(FakeResponse({"items": []}))
    assert github_repos(query=" ")["error"] == "ValueError"
    assert calls == []

    github_repos(query="llm", language="C++ \" OR evil:", sort="popularity", created_within="decade", limit=-4)
    params = calls[0]["params"]
    assert params["q"] == 'llm language:"C++  OR evil"'  # quotes/colons stripped from the qualifier
    assert params["sort"] == "stars"  # out-of-enum -> default
    assert params["per_page"] == 1


def test_github_repos_rate_limit_returns_error_dict(fake_http, monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fake_http(FakeResponse(status_code=403))
    assert github_repos(query="agent")["error"] == "HTTPError"


# ---------------- hf_models ----------------

def test_hf_models_task_and_sort_mapping(fake_http) -> None:
    calls = fake_http(FakeResponse([
        {"id": "black-forest-labs/FLUX.1-dev", "pipeline_tag": "text-to-image", "downloads": 9, "likes": 3},
        {"downloads": 1},
    ]))
    result = hf_models(task="Text to Image", sort="trending", limit=3)

    assert calls[0]["url"] == "https://huggingface.co/api/models"
    assert calls[0]["params"] == {"sort": "trendingScore", "direction": -1, "limit": 3, "pipeline_tag": "text-to-image"}
    assert len(result["items"]) == 1
    assert result["items"][0]["url"] == "https://huggingface.co/black-forest-labs/FLUX.1-dev"
    assert result["items"][0]["metrics"] == {"downloads": 9, "likes": 3}


def test_hf_models_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"error": "not a list"}))
    assert hf_models(query="", task="")["error"] == "ValueError"
    assert calls == []

    result = hf_models(query="whisper", sort="most downloaded", limit="50")
    assert calls[0]["params"]["sort"] == "downloads"
    assert calls[0]["params"]["limit"] == 20
    assert calls[0]["params"]["search"] == "whisper"
    assert result["items"] == []  # non-list payload handled, no crash


def test_hf_models_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    assert hf_models(query="llama")["error"] == "HTTPError"
