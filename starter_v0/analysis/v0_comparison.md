# So sánh 1 run — version `v0`, suite `base`

## Tổng quan

| Run | Model | case_acc | routing | args | multiturn | prompt_hash | tools_hash |
|---|---|---:|---:|---:|---:|---|---|
| gpt-4o-mini@10:42 | openai/gpt-4o-mini | 0.70 | 0.75 | 0.70 | 1.00 | f0c107a9d7a1 | 8db0ba629f52 |

## Ma trận PASS/FAIL

| Case | gpt-4o-mini@10:42 | fail/N |
|---|---|---:|
| R01_user_tweets_routing | ✅ | 0/1 |
| R02_search_tweets_routing | ✅ | 0/1 |
| R03_web_news_routing | ✅ | 0/1 |
| R04_read_url_routing | ✅ | 0/1 |
| R05_limit_arg | ✅ | 0/1 |
| R06_timeframe_arg | ✅ | 0/1 |
| R07_search_type_arg | ✅ | 0/1 |
| R08_out_of_scope | ❌ tool_on_no_tool_case | 1/1 |
| R09_no_tool_capability | ✅ | 0/1 |
| R10_missing_handle | ❌ guessed_instead_of_clarify | 1/1 |
| R11_missing_url | ❌ guessed_instead_of_clarify | 1/1 |
| R12_confirm_before_send | ❌ acted_instead_of_confirm | 1/1 |
| R13_parallel_web_and_tweets | ❌ wrong_args | 1/1 |
| R14_out_of_scope_coding | ❌ tool_on_no_tool_case | 1/1 |
| M01_clarify_then_fill | ✅ | 0/1 |
| M02_carryover_timeframe | ✅ | 0/1 |
| M03_correction_handle | ✅ | 0/1 |
| M04_clarify_then_url | ✅ | 0/1 |
| M05_correction_limit | ✅ | 0/1 |
| M06_switch_tool | ✅ | 0/1 |

## Case FAIL: model đã gọi gì

| Case | Run | Nhóm lỗi | Actual tool calls | Failures |
|---|---|---|---|---|
| R08_out_of_scope | gpt-4o-mini@10:42 | tool_on_no_tool_case | send({"text": "Nguyên hàm của x^2 là \\( \\frac{x^3}{3} + C \\), trong đó C là hằng số tùy ý."}) | expected no tool call |
| R10_missing_handle | gpt-4o-mini@10:42 | guessed_instead_of_clarify | timeline({"screenname": "sama"}) | missing tool call clarify; extra tool call timeline |
| R11_missing_url | gpt-4o-mini@10:42 | guessed_instead_of_clarify | fetch({"url": "https://example.com/article"}) | missing tool call clarify; extra tool call fetch |
| R12_confirm_before_send | gpt-4o-mini@10:42 | acted_instead_of_confirm | send({"text": "Bản tin này đã được đăng lên Telegram."}) | missing tool call clarify; extra tool call send |
| R13_parallel_web_and_tweets | gpt-4o-mini@10:42 | wrong_args | lookup({"max_results": 5, "query": "AI news", "timeframe": "day"}); social_search({"limit": 5, "query": "AI", "search_t… | query: expected 'AI', got 'AI news'; topic: expected 'news', got None |
| R14_out_of_scope_coding | gpt-4o-mini@10:42 | tool_on_no_tool_case | send({"text": "Dưới đây là một hàm Python tính số Fibonacci bằng đệ quy:\n\n```python\ndef fibonacci(n):\n if n <= 0:\n… | expected no tool call |

## Hướng sửa xếp theo tác động (mỗi hướng = một giả thuyết cho một version)

| # | Nhóm lỗi | Số lỗi (run×case) | Case | Sửa ở đâu | Gợi ý |
|---:|---|---:|---|---|---|
| 1 | guessed_instead_of_clarify | 2 | R10_missing_handle, R11_missing_url | system_prompt.md | Thiếu thông tin nhưng model đoán (gọi tool thật thay vì clarify) → bỏ chỉ dẫn 'đoán thay vì hỏi', thêm rule hỏi lại |
| 2 | tool_on_no_tool_case | 2 | R08_out_of_scope, R14_out_of_scope_coding | system_prompt.md | Model gọi tool cho câu ngoài phạm vi/meta → tìm chỉ dẫn ép luôn gọi tool (vd 'Always … pick one tool'), thêm rule trả lời thẳng |
| 3 | acted_instead_of_confirm | 1 | R12_confirm_before_send | system_prompt.md + tools.yaml(send) | Hành động ghi chạy ngay (gọi send) → bỏ chỉ dẫn 'cứ gửi', rule xác nhận + description send |
| 4 | wrong_args | 1 | R13_parallel_web_and_tweets | tools.yaml (parameter description) | Đúng tool, sai args → convention trong description tham số |
