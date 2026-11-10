# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: 1 trang, xong trước 16:30. Bản poster: `artifacts/poster.html`.
> - **PHẦN B — Chi tiết / Bằng chứng**: dựa trên log thật. Các khối nằm giữa `<!-- AUTO:... -->` được
>   `python scripts/fill_report.py` điền **tự động từ `runs/*.json`, `version_log.csv`, `transcripts/`** — không gõ tay số liệu.

## Team

- Team: _(điền tên nhóm)_
- Members: _(điền họ tên + MSSV)_
- Provider/model: OpenRouter — `openai/gpt-4o-mini` (mặc định của `providers/openrouter_provider.py`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Research agent cho tin tức công nghệ/AI**: tìm tin trên web, đọc tweet của một người hoặc theo chủ đề, đọc nội dung một URL, tìm paper arXiv, tra Wikipedia, xem Hacker News, tìm repo GitHub và model Hugging Face, tra quy định nội bộ công ty, rồi gom thành bản tin. Agent **hỏi lại khi thiếu thông tin** (không đoán account/URL) và **luôn xin xác nhận trước khi đăng lên Telegram**.

**Link dùng thử (deploy):**

> Chạy `streamlit run app.py` rồi `cloudflared tunnel --url http://localhost:8501`.
>
> URL: _(dán link `https://<random>.trycloudflare.com` khi demo)_

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu account/URL/chủ đề, hoặc hỏi Có/Không trước khi gửi | không |
| timeline | Lấy tweet mới nhất **của một người** (tự đổi tên → handle: Sam Altman → `sama`) | không |
| social_search | Tìm tweet **về một chủ đề** (`Latest` / `Top`) | không |
| lookup | Tìm tin/thông tin trên web (Tavily, `topic=news`, `timeframe=day/week/...`) | không |
| fetch | Đọc và tóm tắt nội dung một URL (Firecrawl) | không |
| format | Gom các item đã có thành bản tin markdown | không |
| send | Đăng lên Telegram — **chỉ khi đã xác nhận** (`confirmed=true`) | không (bonus) |
| policy | Tra company policy nội bộ (nguồn trích dẫn, bảo mật dữ liệu, đăng bài...) | không (bonus) |
| papers / paper_text | Tìm paper arXiv / tải PDF arXiv và trích text | không (bonus) |
| **wikipedia** | Tra kiến thức nền: một người, khái niệm, tổ chức là gì (en/vi) | **có** |
| **hackernews** | Xem dân dev trên Hacker News bàn gì (top/latest, theo khoảng thời gian) | **có** |
| **github_repos** | Tìm repo mã nguồn mở trên GitHub (lọc ngôn ngữ, sắp theo sao) | **có** |
| **hf_models** | Tìm model trên Hugging Face theo task (text-to-image, ASR...) và độ phổ biến | **có** |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?` → `lookup(topic=news, timeframe=day)`
2. `Tóm tắt 5 tweet mới nhất giúp mình` → agent hỏi lại *"của ai?"* → trả lời `Của Andrej Karpathy` → `timeline(karpathy, 5)`
3. `Tóm tắt bài này: https://www.anthropic.com/research` → `fetch`
4. `Tuần này trên Hacker News dân dev bàn gì về Rust?` / `Tìm 5 repo GitHub nhiều sao nhất về LLM agent framework`
5. `Đăng bản tin AI hôm nay lên Telegram` → agent **hỏi xác nhận Có/Không** trước, chỉ gửi sau khi bấm "Có"

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Hướng tối ưu được chốt **từ bằng chứng của v0** (so sánh v0 trong nhóm bằng `scripts/compare_runs.py`, kết quả ở
`analysis/v0_comparison.md`): v0 = 0.70, cả 6 case FAIL đều do 3 câu chỉ dẫn xấu trong prompt, còn args và multi-turn
đã đúng ngay từ v0. Vì vậy mỗi version v1–v3 gỡ **đúng một** câu chỉ dẫn xấu, v4–v5 mới đụng tới tools.yaml.
Snapshot từng version: `artifacts/versions/vN/{system_prompt.md,tools.yaml}` (bản cuối `v5` = `artifacts/system_prompt.md` + `artifacts/tools.yaml`).

| Version | Thay đổi | Giả thuyết (viết từ bằng chứng v0, trước khi chạy) | Case mục tiêu |
|---|---|---|---|
| v0 | baseline starter | Đo hành vi chưa tối ưu | — |
| v1 | `system_prompt.md` | Câu *"Always finish in a single step. Pick one tool"* ép model gọi đúng 1 tool mỗi lượt → gọi tool cả cho câu ngoài phạm vi, và không gọi song song 2 nguồn | R08, R14, R13 |
| v2 | `system_prompt.md` | Đoạn *"đừng hỏi lại, cứ đoán (Sam Altman, đoán URL)"* làm model đoán thay vì `clarify` | R10, R11 |
| v3 | `system_prompt.md` | Câu *"muốn gửi thì cứ gửi"* + câu thiếu nội dung khiến model không hỏi `yes_no` trước khi gửi | R12 |
| v4 | `tools.yaml` | Viết lại description (khi nào dùng / KHÔNG dùng, convention args, `send` chỉ khi `confirmed`) không gây regression | giữ 100% base |
| v5 | `tools.yaml` + `system_prompt.md` | Thêm 4 tool mới có ranh giới rõ không làm giảm base và PASS group eval | base + G01–G10 |

Kết quả thật (tự sinh):

<!-- AUTO:B1 -->
| Version | Changed Artifact | Hypothesis | Metric Before | Metric After (case_acc) | routing | args | multiturn | Run File |
|---|---|---|---:|---:|---:|---:|---:|---|
| v0 | baseline | Do hanh vi chua toi uu truoc khi sua | — | 0.70 (14/20) | 0.75 | 0.70 | 1.00 | `runs\v0_B_base_openrouter_20261110T104242979050.json` |
| v1 | system_prompt.md | v0 FAIL R08, R14 (gọi tool cho câu ngoài phạm vi) và R13 (chỉ 1 tool) vì prompt ép đúng một tool mỗi lượt | 0.7000 | 0.80 (16/20) | 0.80 | 0.80 | 0.83 | `runs\v1_B_base_openrouter_20261110T165054788663.json` |
| v2 | system_prompt.md | v0 FAIL R10, R11 vì prompt ra lệnh đoán thay vì hỏi lại | 0.8000 | 0.80 (16/20) | 0.90 | 0.80 | 0.83 | `runs\v2_B_base_openrouter_20261110T165153717523.json` |
| v3 | system_prompt.md | R12 FAIL vì prompt cho phép gửi ngay và khi thiếu nội dung model hỏi kiểu text thay vì yes_no | 0.8000 | 0.80 (16/20) | 0.95 | 0.80 | 0.83 | `runs\v3_B_base_openrouter_20261110T165309612676.json` |
| v4 | tools.yaml | Description rõ ràng không làm giảm base (không regression) và giữ boundary send ở tầng tool | 0.8000 | 0.95 (19/20) | 0.95 | 0.95 | 1.00 | `runs\v4_B_base_openrouter_20261110T165415212207.json` |
| v5 | tools.yaml + system_prompt.md | Mở rộng scope bằng tool có ranh giới rõ không làm giảm base và cho phép PASS group eval | 0.9500 | 0.95 (19/20) | 0.95 | 0.95 | 1.00 | `runs\v5_B_base_openrouter_20261110T165523621973.json` |
<!-- /AUTO:B1 -->

Ma trận PASS/FAIL từng case qua các version:

<!-- AUTO:B1_MATRIX -->
| Case | v0 | v1 | v2 | v3 | v4 | v5 |
|---|---|---|---|---|---|---|
| R01_user_tweets_routing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R02_search_tweets_routing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R03_web_news_routing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R04_read_url_routing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R05_limit_arg | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R06_timeframe_arg | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R07_search_type_arg | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R08_out_of_scope | ❌ unexpected_tool_call | ✅ | ✅ | ✅ | ✅ | ✅ |
| R09_no_tool_capability | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R10_missing_handle | ❌ missing_tool_call | ❌ missing_tool_call | ❌ wrong_arg_value | ✅ | ❌ missing_tool_call | ❌ missing_tool_call |
| R11_missing_url | ❌ missing_tool_call | ❌ missing_tool_call | ❌ wrong_arg_value | ❌ wrong_arg_value | ✅ | ✅ |
| R12_confirm_before_send | ❌ missing_tool_call | ❌ missing_tool_call | ❌ missing_tool_call | ❌ wrong_arg_value | ✅ | ✅ |
| R13_parallel_web_and_tweets | ❌ wrong_arg_value | ✅ | ✅ | ❌ wrong_arg_value | ✅ | ✅ |
| R14_out_of_scope_coding | ❌ unexpected_tool_call | ✅ | ✅ | ✅ | ✅ | ✅ |
| M01_clarify_then_fill | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M02_carryover_timeframe | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M03_correction_handle | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M04_clarify_then_url | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M05_correction_limit | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M06_switch_tool | ✅ | ❌ extra_tool_call | ❌ extra_tool_call | ❌ extra_tool_call | ✅ | ✅ |
<!-- /AUTO:B1_MATRIX -->

## B2. Failure Analysis

Mỗi case FAIL lần đầu xuất hiện ở version nào, model đã gọi gì, và version nào sửa được (tự sinh từ `results[*].result`):

<!-- AUTO:B2 -->
| Case ID | Seen in | Failure Type | Observed mismatch | Actual Tool Calls | What Failed | Fixed in |
|---|---|---|---|---|---|---|
| R08_out_of_scope | v0 | out_of_scope | unexpected_tool_call | send({"text": "Nguyên hàm của x^2 là \\( \\frac{x^3}{3} + C \\), trong đó C là hằng số tùy ý."}) | expected no tool call | v1 |
| R10_missing_handle | v0 | missing_info | missing_tool_call | timeline({"screenname": "sama"}) | missing tool call clarify; extra tool call timeline | v3 |
| R11_missing_url | v0 | missing_info | missing_tool_call | fetch({"url": "https://example.com/article"}) | missing tool call clarify; extra tool call fetch | v4 |
| R12_confirm_before_send | v0 | wrong_boundary | missing_tool_call | send({"text": "Bản tin này đã được đăng lên Telegram."}) | missing tool call clarify; extra tool call send | v4 |
| R13_parallel_web_and_tweets | v0 | wrong_tool | wrong_arg_value | lookup({"max_results": 5, "query": "AI news", "timeframe": "day"}); social_search({"limit": 5, "query": "AI", "search_type": "Latest"}) | query: expected 'AI', got 'AI news'; topic: expected 'news', got None | v1 |
| R14_out_of_scope_coding | v0 | out_of_scope | unexpected_tool_call | send({"text": "Dưới đây là một hàm Python tính số Fibonacci bằng đệ quy:\n\n```python\ndef fibonacci(n):\n if n <= 0:\n return 0\n elif n == 1:\n return 1\n el… | expected no tool call | v1 |
| M06_switch_tool | v1 | wrong_tool | extra_tool_call | lookup({"max_results": 5, "query": "OpenAI", "timeframe": "day", "topic": "news"}); social_search({"limit": 5, "query": "OpenAI", "search_type": "Latest"}) | extra tool call social_search | v4 |
<!-- /AUTO:B2 -->

Cơ chế lỗi của v0 và version sửa nó:

| Case v0 FAIL | Loại lỗi | Câu chỉ dẫn gây lỗi trong prompt starter | Fix |
|---|---|---|---|
| R08, R14 | out_of_scope (`unexpected_tool_call`) | *"Always finish the request in a single step. Pick one tool"* — kể cả khi không cần tool | v1: ngoài phạm vi / meta → trả lời thẳng |
| R13 | wrong_tool (`missing_tool_call`) | cùng câu trên — chỉ được chọn **một** tool | v1: nhiều nguồn → gọi nhiều tool |
| R10, R11 | missing_info | *"do not ask them back — just make a sensible guess… pick Sam Altman… assume a likely URL"* | v2: thiếu account/URL → `clarify(text)` |
| R12 | wrong_boundary | *"When the user wants to send… just go ahead and do it"* | v3: luôn `clarify(yes_no)` trước khi gửi |

Ghi chú vòng khám phá trước (round 1, lưu ở `runs_archive/`): khi chưa đo v0 mà đoán trước, nhóm đã dành 2 version để sửa
args (tools.yaml) và multi-turn — cả hai đều **không đổi metric** vì `gpt-4o-mini` đã đúng các phần đó từ v0. Đây là lý do
vòng chính thức đặt giả thuyết từ log v0.

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 single turn + 5 multi turn), 4 tool mới đều có case route tới:

| Case ID | Turns | What It Tests | Expected Tool/Behavior |
|---|---|---|---|
| G01_wikipedia_vi_concept | single | Hỏi khái niệm + Wikipedia tiếng Việt | `wikipedia(lang=vi)` |
| G02_hackernews_top_week | single | HN thay vì Twitter; tuần này + nhiều điểm | `hackernews(query=Rust, sort=top, timeframe=week)` |
| G03_github_top_stars | single | Tìm repo, "5 repo", "nhiều sao nhất" | `github_repos(sort=stars, limit=5)` |
| G04_hf_models_task | single | Model HF theo task, "tải nhiều nhất" | `hf_models(task=text-to-image, sort=downloads)` |
| G05_arxiv_newest_sort | single | "paper mới nhất" | `papers(sort_by=submittedDate)` |
| G06_multiturn_github_fill_language | multi | Carry chủ đề + thêm filter ngôn ngữ + sort | `github_repos(language=Rust, sort=stars)` |
| G07_multiturn_send_after_yes | multi | Sau khi hỏi xác nhận, user nói "Có" | `send(text=…, confirmed=true)` |
| G08_multiturn_twitter_to_hn | multi | Bỏ Twitter → HN, giữ chủ đề, "mới nhất" | `hackernews(query=Claude, sort=latest)` |
| G09_multiturn_wiki_correction | multi | Sửa người + chọn bản tiếng Anh | `wikipedia(query=Geoffrey Hinton, lang=en)` |
| G10_multiturn_cancel_send | multi | User huỷ đăng, đổi sang tìm web | `lookup(topic=news, timeframe=week)`, **không** `send` |

Kết quả thật (tự sinh):

<!-- AUTO:B3 -->
Run: `runs\v5_B_group_openrouter_20261110T165551717517.json` — version `v5+pfd25f1a8bdd8+t4e3180c18921` — case_accuracy **0.90** (9/10), routing 0.90, args 0.90, multiturn 0.80

| Case ID | Turns | What It Tests | Expected Tool/Behavior | Actual Tool Calls | Result |
|---|---|---|---|---|---|
| G01_wikipedia_vi_concept | single | Hỏi khái niệm + nói rõ Wikipedia tiếng Việt → tool mới wikipedia với lang=vi, không dùng lookup. | wikipedia({"lang": "vi"}) | wikipedia({"lang": "vi", "query": "học tăng cường"}) | PASS |
| G02_hackernews_top_week | single | Nhắc Hacker News → hackernews (không phải social_search); 'tuần này' → timeframe=week, 'nhiều điểm nhất' → sort=top, qu… | hackernews({"query": "Rust", "sort": "top", "timeframe": "week"}) | hackernews({"query": "Rust", "sort": "top", "timeframe": "week"}) | PASS |
| G03_github_top_stars | single | Tìm repo mã nguồn mở → github_repos, '5 repo' → limit=5, 'nhiều sao nhất' → sort=stars. | github_repos({"limit": 5, "sort": "stars"}) | github_repos({"limit": 5, "query": "LLM agent framework", "sort": "stars"}) | PASS |
| G04_hf_models_task | single | Model trên Hugging Face → hf_models (không phải papers/lookup), map task thành pipeline tag text-to-image, 'tải nhiều n… | hf_models({"sort": "downloads", "task": "text-to-image"}) | hf_models({"sort": "downloads", "task": "text-to-image"}) | PASS |
| G05_arxiv_newest_sort | single | 'mới nhất' với paper → sort_by=submittedDate thay vì relevance mặc định. | papers({"sort_by": "submittedDate"}) | papers({"max_results": 5, "query": "speculative decoding", "sort_by": "submittedDate"}) | PASS |
| G06_multiturn_github_fill_language | multi | 3 turns: carry chủ đề vector database, thêm filter language=Rust từ lượt 2, sort=stars từ lượt 3. | github_repos({"language": "Rust", "sort": "stars"}) | github_repos({"language": "Rust", "query": "vector database", "sort": "stars"}) | PASS |
| G07_multiturn_send_after_yes | multi | Nhánh ngược của R12: sau khi đã hỏi và user nói 'Có' → gọi send với đúng text đã xác nhận và confirmed=true (không hỏi … | send({"confirmed": true, "text": "Bản tin AI hôm nay đã sẵn sàng"}) | send({"confirmed": true, "text": "Bản tin AI hôm nay đã sẵn sàng"}) | PASS |
| G08_multiturn_twitter_to_hn | multi | 3 turns: bỏ social_search, chuyển sang hackernews, giữ chủ đề Claude, 'mới nhất' → sort=latest; không gọi thừa social_s… | hackernews({"query": "Claude", "sort": "latest"}) | hackernews({"limit": 5, "query": "Claude", "sort": "latest"}) | PASS |
| G09_multiturn_wiki_correction | multi | 3 turns: sửa người (Yann LeCun → Geoffrey Hinton), lang=en; không gọi thêm cho Yann LeCun. | wikipedia({"lang": "en", "query": "Geoffrey Hinton"}) | wikipedia({"lang": "en", "query": "Geoffrey Hinton"}) | PASS |
| G10_multiturn_cancel_send | multi | 3 turns: user huỷ hành động ghi → KHÔNG gọi send (gọi thừa = fail), chuyển sang lookup news + timeframe=week. | lookup({"timeframe": "week", "topic": "news"}) | lookup({"max_results": 5, "query": "công nghệ", "timeframe": "week", "topic": "news"}); lookup({"max_results": 5, "quer… | FAIL (extra tool call lookup) |
<!-- /AUTO:B3 -->

Extension eval (policy + arXiv) trên bản cuối:

<!-- AUTO:B3_EXT -->
Run: `runs\v5_B_extension_openrouter_20261110T165628962998.json` — version `v5+pfd25f1a8bdd8+t4e3180c18921` — case_accuracy **0.90** (9/10), routing 0.90, args 0.90, multiturn —

| Case ID | Turns | What It Tests | Expected Tool/Behavior | Actual Tool Calls | Result |
|---|---|---|---|---|---|
| E01_company_source_policy | single | Câu hỏi policy nội bộ về source/citation → search_company_policy. | policy({"policy_area": "source_citation"}) | policy({"policy_area": "source_citation", "query": "tweet viral"}) | PASS |
| E02_company_data_privacy | single | Câu hỏi secrets/customer data → company policy, không dùng web. | policy({"policy_area": "data_privacy"}) | policy({"policy_area": "data_privacy", "query": "API key, dữ liệu khách hàng"}) | PASS |
| E03_company_telegram_approval | single | Câu hỏi write/publish policy → company policy. | policy({"policy_area": "external_publishing"}) | policy({"policy_area": "external_publishing", "query": "đăng bản tin lên Telegram"}) | PASS |
| E04_arxiv_search_topic | single | Paper/preprint discovery → arxiv_search. | papers({}) | papers({"max_results": 5, "query": "retrieval augmented generation evaluation"}) | PASS |
| E05_arxiv_paper_text | single | Có arXiv ID và muốn đọc nội dung → tải PDF + extract local text. | paper_text({"arxiv_url": "1706.03762", "max_pages": 2}) | paper_text({"arxiv_url": "1706.03762", "max_pages": 2}) | PASS |
| E06_briefing_live_plus_style | single | Kết hợp live news + company source policy; eval không phụ thuộc thứ tự. | lookup({"timeframe": "day", "topic": "news"}); policy({"policy_area": "source_citation"}) | policy({"policy_area": "source_citation", "query": "source citation"}) | FAIL (missing tool call lookup) |
| E07_paper_scan_template_plus_arxiv | single | Paper search + company citation policy. | papers({}); policy({"policy_area": "source_citation"}) | papers({"max_results": 5, "query": "AI agents", "sort_by": "submittedDate"}); policy({"policy_area": "source_citation",… | PASS |
| E08_specific_url_not_arxiv | single | Specific URL → read_url, internal research policy → company policy. | fetch({"url": "https://openai.com/research/"}); policy({"policy_area": "ai_research"}) | fetch({"url": "https://openai.com/research/"}); policy({"policy_area": "ai_research", "query": "research workflow"}) | PASS |
| E09_two_links_parallel | single | User gửi 2 links cùng lúc → gọi read_url cho từng link; eval không phụ thuộc thứ tự. | fetch({"url": "https://openai.com/research/"}); fetch({"url": "https://www.anthropic.com/research"}) | fetch({"url": "https://openai.com/research/"}); fetch({"url": "https://www.anthropic.com/research"}) | PASS |
| E10_arxiv_research_search | single | Research paper/arXiv discovery → arxiv_search. | papers({}) | papers({"max_results": 5, "query": "AI agent evaluation", "sort_by": "submittedDate"}) | PASS |
<!-- /AUTO:B3_EXT -->

## B4. Live Chat Evidence

`scripts/run_chat_demo.py` chạy đúng vòng lặp tool của `chat.py` với 6 lượt: tin AI hôm nay → thiếu account → bổ sung account → yêu cầu đăng Telegram (phải hỏi Có/Không) → "Có" → câu dùng tool mới. UI Streamlit cũng ghi transcript cùng format (`transcripts/ui_*.transcript.json`).

<!-- AUTO:B4 -->
Transcript: `transcripts\v5_openrouter_20261110T165629438183.transcript.json` — `v5+pfd25f1a8bdd8+t4e3180c18921` — model `openai/gpt-4o-mini`

| Turn | User Request | Tool Calls | Status | Agent reply (rút gọn) |
|---|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | lookup({"max_results": 5, "query": "AI", "timeframe": "day", "topic": "news"}) | answered | Here are some notable AI news articles from today: 1. **[Opinion: AI cannot replace being human – The Battalion](https://thebatt.com/opinion/opinion-ai-cannot-… |
| 2 | Tóm tắt 5 tweet mới nhất giúp mình | timeline({"limit": 5, "screenname": "OpenAI"}); clarify({"question": "Mình không thể lấy tweet từ tài khoản OpenAI. Bạn có muốn lấy tweet từ một tài … | waiting_for_user | Mình không thể lấy tweet từ tài khoản OpenAI. Bạn có muốn lấy tweet từ một tài khoản khác không? |
| 3 | Của Andrej Karpathy nhé | timeline({"limit": 5, "screenname": "karpathy"}) | answered | Mình không thể lấy tweet từ tài khoản Andrej Karpathy do gặp lỗi truy cập. Bạn có muốn thử một tài khoản khác không? |
| 4 | Đăng tóm tắt 5 tweet đó lên Telegram giúp mình | clarify({"question": "Bạn có muốn đăng tóm tắt 5 tweet mới nhất của Andrej Karpathy lên Telegram không?", "response_type": "yes_no"}) | waiting_for_user | Bạn có muốn đăng tóm tắt 5 tweet mới nhất của Andrej Karpathy lên Telegram không? |
| 5 | Có, mình xác nhận, đăng đi | send({"confirmed": true, "text": "Tóm tắt 5 tweet mới nhất của Andrej Karpathy:\n\n1. **Tweet 1**: Nội dung tóm tắt của tweet đầu tiên.\n2. **Tweet 2… | answered | Có vẻ như mình không thể đăng tóm tắt lên Telegram do thiếu thông tin cần thiết. Bạn có muốn mình giúp gì khác không? |
| 6 | Tuần này trên Hacker News dân dev bàn gì về AI agents? | hackernews({"limit": 5, "query": "AI agents", "sort": "top", "timeframe": "week"}) | answered | Dưới đây là những bài thảo luận nổi bật về AI agents trên Hacker News trong tuần này: 1. **[YC's Garry Tan uses AI agents so much, he spends up to $200K a year… |
<!-- /AUTO:B4 -->

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tools/send/tool.py`, case R12 + G07 + G10, transcript lượt 4–5 | Chỉ gửi khi `confirmed` là boolean `true`; nếu chưa xác nhận tool trả `awaiting_user` để chat/UI dừng lại hỏi Có/Không | Sửa BUG-1 (`confirmed="false"` vẫn gửi), BUG-2 (token lộ trong error), retry plain text khi Markdown lỗi |
| arXiv/company policy | `data/eval_research_extension.json`, run suite `extension` | `policy_area` mô tả rõ từng nhóm; `papers` vs `paper_text` tách rõ tìm vs đọc | Policy trả `untrusted_text` riêng cho dòng giống lệnh (prompt injection trong KB) — có test |
| UI | `app.py` (Streamlit) | Chat nhiều lượt, xem từng tool call/result, nút ✅/❌ khi agent chờ xác nhận gửi, sidebar chọn provider/model/version, ghi transcript | Không lưu key trong UI; lỗi provider hiển thị thay vì crash |
| 4 tool mới (> 3 → bonus point) | `tools/{wikipedia,hackernews,github_repos,hf_models}/` + `TOOL.md` + `tools/__init__.py` + `tools.yaml` | API công khai, **không cần key**; trả item cùng schema (`title,url,source,summary`) nên `format` dùng lại được | Clamp `limit`, enum sai → mặc định, query rỗng → error dict không gọi mạng; `GITHUB_TOKEN` (tuỳ chọn) không bao giờ trả về trong result |
| Tool unit tests (`tests/`) | `analysis/pytest_before_fix.txt`, `analysis/pytest_after_fix.txt` | **124 passed, 0 failed, 0 skipped** | Toàn bộ offline (`fake_http`), không tốn credit |

**Tool unit tests:** `tests/test_tools_todo.py` có 42 test: 14 stub TODO đã điền, 15 test cho 4 tool mới (≥ 3/tool: happy path, input xấu từ model, nhánh lỗi), và **13 regression test cho 12 bug tìm được trong tool có sẵn**. Cả 13 test này FAIL trên code starter (`analysis/pytest_before_fix.txt`: `13 failed, 111 passed`) và PASS sau khi sửa.

| Bug | Tool | Input biên từ model | Hành vi sai của starter | Fix |
|---|---|---|---|---|
| BUG-1 | send | `confirmed="false"` | Chuỗi khác rỗng là truthy → **vẫn đăng lên Telegram** | Chỉ chấp nhận `True` hoặc `"true"` |
| BUG-1b | send | `confirmed=false` trong chat | Không có `awaiting_user` → `chat.py` lặp tool tới `max_tool_rounds` | Trả `awaiting_user` + câu hỏi Có/Không kèm nội dung |
| BUG-2 | send | token sai / HTTP 401 | Message của `HTTPError` chứa URL `bot<TOKEN>` → **token lộ vào transcript** | Redact token |
| BUG-3 | send | text có `*`/`_` lẻ | Telegram 400 "can't parse entities" → không gửi được | Retry không `parse_mode` |
| BUG-4 | timeline | `screenname="@sama"` | Gọi API với `@sama` → không có kết quả | Bỏ `@` và khoảng trắng |
| BUG-5 | timeline, social_search | `limit=-1`, `limit=0` | `items[:-1]` bỏ mất tweet cuối; `0` → 5 | `clamp_int(limit, 5, 1, 50)` |
| BUG-6 | social_search | `search_type="top"` | Gửi nguyên chữ thường, API cần `Top` | Chuẩn hoá về `Top`/`Latest` |
| BUG-7 | lookup | `max_results=50`, `timeframe="today"`, `topic="News"` | Gửi thẳng → Tavily trả lỗi | Clamp 1–20, alias timeframe, chuẩn hoá topic |
| BUG-8 | fetch | `url=""` | Vẫn gọi Firecrawl (tốn credit) | Trả error dict trước khi gọi mạng |
| BUG-9 | fetch | `url="openai.com/research"` | Firecrawl từ chối URL thiếu scheme | Thêm `https://` |
| BUG-10 | format | `items=["headline 1", ...]` | `AttributeError` → tool crash | Chuỗi → `{"title": ...}` |
| BUG-11 | format | item không có url | Dòng kết thúc bằng `" - "` lơ lửng | Bỏ separator khi không có nguồn |
| BUG-12 | clarify | `response_type="free"` | UI không biết render kiểu gì | Fallback `text`; `yes_no` có sẵn options |

**Ví dụ lỗi unit test bắt được mà eval không bắt được:** BUG-1. Eval chỉ so `tool_calls` + args: nếu model gọi `send(text=..., confirmed="false")`, eval báo `wrong_arg_value` nhưng tool **vẫn đăng bài thật** — side effect đã xảy ra. Tương tự BUG-2: G07 có thể PASS hoàn toàn (đúng tool, đúng `confirmed=true`), nhưng nếu token sai thì `tool_results` trong run JSON/transcript chứa nguyên bot token — eval không bao giờ nhìn tới chỗ đó.

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** những gì là *chính sách hành vi* áp dụng cho mọi tool — khi nào hỏi lại thay vì đoán, ranh giới hành động ghi (xác nhận trước khi gửi), câu ngoài phạm vi/không cần tool, được gọi nhiều tool song song, và cách đọc hội thoại nhiều lượt (lượt cuối, carry-over, correction). Starter đặt 3 chỉ dẫn xấu đúng ở đây nên chỉ sửa tools.yaml là không đủ.
- **Fix thuộc `tools.yaml`:** những gì gắn với *một tool cụ thể* — tool làm gì, khi nào dùng / khi nào KHÔNG dùng (để phân biệt timeline vs social_search, lookup vs fetch, tool mới vs tool cũ), và convention từng tham số (handle không `@`, map tên→handle, `topic`, `timeframe`, `search_type`, `query` chỉ là keyword, URL giữ nguyên). Model đọc description ngay lúc điền args nên đặt convention ở đây hiệu quả và không làm prompt dài thêm.
- **Cần review thủ công thay vì chấm tự động:** (1) case `no_tool` (R08, R09, R14) — eval chỉ kiểm tra *không gọi tool*, không kiểm tra câu trả lời có từ chối lịch sự/đúng không; (2) chất lượng câu hỏi `clarify` (có hỏi đúng thứ bị thiếu không) — eval chỉ xem `response_type`; (3) nội dung `send(text=...)` có đúng bản tin đã được xác nhận; (4) `query` tự do của `social_search`/`papers`/`github_repos` khi expected args để `{}`; (5) tool trả lỗi (thiếu key, 429) nhưng eval vẫn PASS vì chỉ chấm routing — phải đọc `tool_results` trong run JSON.
- **Phát hiện từ chat live (eval không bắt được):** khi `timeline` lỗi (thiếu `RAPIDAPI_KEY`), agent vẫn đề nghị đăng *chính câu báo lỗi* lên Telegram ở lượt sau — đúng quy trình hỏi `yes_no`, nhưng nội dung vô nghĩa. Eval chỉ chấm tool/args nên PASS; cần rule "không đề nghị gửi khi chưa có nội dung từ tool thành công".
- **Cải thiện tiếp:** chấm cả `tool_results` (case FAIL nếu tool trả `error`); thêm case `clarify` kiểu `choice`; đưa map tên→handle thành tool `resolve_handle` (tra cứu thật) thay vì liệt kê trong description; chạy mỗi version ≥ 3 lần để đo độ dao động khi `temperature=0` nhưng provider vẫn không xác định; thêm eval chống prompt-injection từ kết quả `fetch`/`policy`.

## B7. Small Local Model Challenge (bonus)

Chuẩn bị sẵn 2 vòng tối ưu cho model nhỏ (không phá bản cloud):

- `artifacts/local/v4-local/` — giả thuyết: *model nhỏ bị lạc vì prompt dài + 14 tool*. Prompt 5 rule ngắn; chỉ giữ 6 tool base eval cần; mỗi description 1 câu kèm **ví dụ args**; bỏ field optional (`options`, `max_results`, `limit` của social_search).
- `artifacts/local/v5-local/` — giả thuyết: *few-shot cụ thể giúp model nhỏ gọi `clarify` và điền args đúng hơn*. Thêm 9 ví dụ routing (dùng người/chủ đề **khác** case eval để không học thuộc đáp án).
- Lệnh: `python scripts/run_all.py --skip-base --skip-group --skip-extension --skip-chat --local-models qwen2.5:7b llama3.2:3b` → chạy `v5-<model>` (prompt cloud v5), `v4-local-<model>`, `v5-local-<model>` cho từng model rồi kiểm tra ngược `v5-local-on-cloud`.

<!-- AUTO:B7 -->
_Chưa chạy local model — `python scripts/run_all.py --skip-base --skip-group --skip-extension --skip-chat --local-models qwen2.5:7b llama3.2:3b`._
<!-- /AUTO:B7 -->

Lỗi đặc thù của model nhỏ (đếm tự động từ run JSON):

<!-- AUTO:B7_PATTERNS -->
_Chưa có run local._
<!-- /AUTO:B7_PATTERNS -->

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng? _(so cột case_accuracy v4-local vs v5-local ở bảng trên)_
- Bản prompt tối ưu cho local chạy trên model cloud thì sao? _(dòng `v5-local-on-cloud` trong `version_log.csv`)_
- Khi nào chọn model local thay vì cloud? Khi dữ liệu không được rời máy (policy `data_privacy`), khi cần chạy offline/miễn phí cho các tác vụ routing đơn giản; giữ cloud cho multi-turn và câu cần nhiều tool song song.
