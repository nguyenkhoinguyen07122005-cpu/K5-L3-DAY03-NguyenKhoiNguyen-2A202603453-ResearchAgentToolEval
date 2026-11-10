# Hướng dẫn chạy để có bằng chứng thật

Mọi phần **không cần API key** đã xong (prompt/tools v0→v5, 4 tool mới, 124 unit test xanh, 10 eval case,
UI Streamlit, poster, REPORT). Các bước dưới đây cần key thật để tạo `runs/*.json`, `transcripts/*.json`,
`artifacts/version_log.csv` — **không được tự bịa số liệu**.

## 1. Setup (một lần)

```bash
cd starter_v0
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env
```

Điền `.env`: `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY`
(+ tuỳ chọn `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GITHUB_TOKEN`). 4 tool mới không cần key.

```bash
pytest                                            # kỳ vọng: 124 passed, 0 skipped
python scripts/preflight_provider.py --provider openrouter
```

## 2. Một lệnh chạy hết

```bash
python scripts/run_all.py --provider openrouter --author "Tên nhóm"
```

Lệnh này lần lượt:

1. chạy base eval cho `v0, v1, v2, v3, v4, v5` (dùng snapshot `artifacts/versions/vN/`);
2. chạy group eval (10 case) + extension eval trên `v5`;
3. ghi `artifacts/version_log.csv` (hash + metric thật lấy từ run JSON);
4. chạy chat demo 6 lượt → `transcripts/*.transcript.json`;
5. `analysis/all_runs.csv` + tự điền các bảng `<!-- AUTO -->` trong `artifacts/REPORT.md`.

Chi phí: mỗi lượt base = 20 lần gọi model + tool thật (Tavily/RapidAPI/Firecrawl). ⚠️ Case `G07` gọi `send`
với `confirmed=true` → nếu đã điền key Telegram thì **sẽ đăng thật** lên channel test của nhóm (đúng là bằng chứng bonus).

Chạy lại từng phần: `--versions v2 v3`, `--skip-base`, `--skip-group`, `--skip-extension`, `--skip-chat`, `--skip-preflight`.

## 3. Đọc kết quả rồi lặp (vòng evidence-driven)

- Mở `artifacts/REPORT.md` → bảng B1 (metric từng version), ma trận PASS/FAIL, B2 (case FAIL + tool đã gọi).
- Nếu một version **không** cải thiện như giả thuyết: sửa `artifacts/versions/vN/...`, chạy lại
  `python scripts/run_all.py --versions vN --skip-group --skip-extension --skip-chat` (các dòng version khác trong
  `version_log.csv` được giữ nguyên), rồi sửa cột `hypothesis` cho đúng với điều đã học được.
- Bản cuối luôn copy về `artifacts/system_prompt.md` + `artifacts/tools.yaml` (hiện = `v5`).
- Viết nhận xét thật của nhóm vào B6/B7 dựa trên bảng (phần chữ ngoài marker không bị script ghi đè).

## 4. UI + link cho team khác

```bash
streamlit run app.py                               # http://localhost:8501
cloudflared tunnel --url http://localhost:8501     # copy link https://....trycloudflare.com
```

Dán link vào `REPORT.md` (A1) và `artifacts/poster.html` (thẻ `#url`). Chat trên UI cũng được lưu vào
`transcripts/ui_*.transcript.json`. Chat tay: `python chat.py --provider openrouter --version v5`.

## 5. Bonus: model local (Step 7)

```bash
ollama pull qwen2.5:7b && ollama pull llama3.2:3b
python scripts/run_all.py --skip-base --skip-group --skip-extension --skip-chat \
    --local-models qwen2.5:7b llama3.2:3b
```

Chạy `v5-<model>` (prompt cloud), `v4-local-<model>` (prompt ngắn, 6 tool), `v5-local-<model>` (+ few-shot),
rồi `v5-local-on-cloud` (kiểm tra ngược) → điền B7 tự động.

## 6. Nộp bài

Nộp thư mục `starter_v0/` **trừ** `.env`, `.venv/`, `arxiv_papers/`. Checklist:
`artifacts/{system_prompt.md, tools.yaml, version_log.csv, REPORT.md, poster.html, versions/}`, `data/eval_group.json`,
`tests/`, `runs/*.json`, `transcripts/*.json`, `analysis/*.csv`, `app.py`, `tools/` (4 tool mới), `scripts/`.
Điền tên nhóm/thành viên ở đầu `REPORT.md`.
