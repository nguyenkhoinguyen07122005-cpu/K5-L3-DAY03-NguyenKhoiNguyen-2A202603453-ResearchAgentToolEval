# Day 03 Lab v2 — Research Agent Tool Eval

Trong lab này, nhóm build một research agent nhỏ nhưng chạy thật. Agent nhận request của user, chọn tool, truyền arguments, chạy tool thật, lưu full JSON log, rồi dùng log đó để tối ưu prompt/tool declaration qua nhiều version.

**Loại bài:** Nhóm · **Thời lượng:** khoảng 4 giờ tại lớp · **Deadline:** 23h59 ngày lab (GMT+7), coach có thể gia hạn tối đa 48h

## Mục tiêu học tập

- Viết system prompt và tool declaration để agent chọn đúng tool, truyền đúng arguments, biết hỏi lại khi thiếu thông tin và xin xác nhận trước khi hành động.
- Tối ưu theo vòng lặp dựa trên bằng chứng: chạy eval, đọc run JSON, đặt một giả thuyết, sửa, đo lại.
- Tự viết eval case và unit test để phân biệt lỗi của model (chọn sai tool, sai args) với lỗi của code tool.
- Đưa agent ra UI cho người khác dùng thử và viết báo cáo dựa trên log thật, không dựa vào cảm giác.

Điều cần học không phải là "chatbot trả lời hay". Điều cần học là vòng lặp evidence-driven:

1. Chạy baseline bằng API thật.
2. Đọc run JSON để biết sai tool, sai args, thiếu hỏi lại, hoặc gọi tool thừa.
3. Sửa `artifacts/system_prompt.md` hoặc `artifacts/tools.yaml`.
4. Chạy lại và ghi versioning.
5. Tự viết thêm eval case để đo những lỗi nhóm quan tâm.
6. Viết report dựa trên log thật.

## Thứ tự đọc

1. [RULES.md](RULES.md) — dùng AI, liêm chính, API key, lỗi kỹ thuật.
2. [CHECKPOINTS.md](CHECKPOINTS.md) — 5 checkpoint phải làm và cách tự kiểm tra.
3. [starter_v0/README.md](starter_v0/README.md) — file chạy, lệnh chạy, input/output, file được sửa.
4. [RUBRIC.md](RUBRIC.md) — 100 điểm chính (C1–C8) và bonus ghi riêng.
5. [SUBMISSION.md](SUBMISSION.md) — tên repo, deliverable, checklist, nộp link trên LMS.

Cấu hình API key cho từng tool: [docs/TOOL-SETUP.md](docs/TOOL-SETUP.md).

## Scope

Nhiệm vụ bắt buộc:

- Setup chạy được bằng provider thật.
- Agent có ít nhất 5 tool trong `artifacts/tools.yaml`.
- Chạy base eval.
- Tối ưu ít nhất 3 vòng sau baseline: `v1`, `v2`, `v3`.
- Ghi `artifacts/version_log.csv`.
- Viết thêm ít nhất 1 tool mới (kèm `TOOL.md`, đăng ký trong `tools/__init__.py` và `tools.yaml`).
- Viết unit test cho tool mới (≥ 3 test/tool) và giữ `pytest` xanh — xem [Step 4b](#step-4b--challenge-viết-test-cho-tool).
- Tự viết thêm 10 eval case vào `data/eval_group.json`, trong đó 5 single turn và 5 multi turn.
- Nộp run JSON, transcript JSON, báo cáo.
- Bắt buộc có UI chạy được bằng Streamlit hoặc Vercel.
- Hoàn thành `report/team/group_report.md`: Phần A (giới thiệu agent: tool gì, làm được gì, câu hỏi mẫu) xong **trước 16:30** làm tài liệu phụ trợ khi demo; Phần B (chi tiết) hoàn thiện sau để nộp bài.
- Điền `TEAM.md`; mỗi thành viên viết báo cáo cá nhân `report/team/MSSV_HoTen.md`.

Bonus (ghi riêng, tối đa 10 điểm, chi tiết trong [RUBRIC.md](RUBRIC.md)):

- **Small Local Model Challenge**: chạy agent bằng model local nhỏ (≤ 8B) qua Ollama — xem [Step 7](#step-7--bonus-challenge-small-local-model).
- **Hơn 3 tool mới** (≥ 4 tool do nhóm tự viết, ngoài các tool có sẵn), mỗi tool kèm `TOOL.md` + đăng ký trong `tools/__init__.py` + `tools.yaml` + ≥ 3 test.
- Action tool `send`: gửi thật lên Telegram sau khi user xác nhận, có transcript chứng minh. (Boundary xác nhận trong prompt/`tools.yaml` là phần **bắt buộc**.)
- Test challenge: toàn suite `pytest` 0 skipped, hoặc có regression test cho bug tìm được trong tool có sẵn — xem [Step 4b](#step-4b--challenge-viết-test-cho-tool).

Tool có sẵn (`send`, `policy`, `papers`, `paper_text`) không tự được bonus.

## TODO Checklist

Đánh dấu khi xong. Mỗi dòng trỏ tới file cần sửa và bằng chứng cần nộp.

**Setup (CP1)**
- [ ] `TEAM.md` có tên nhóm và thành viên
- [ ] `.env` có provider key + `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY`
- [ ] `python scripts/preflight_provider.py --provider openrouter` pass
- [ ] `pytest` chạy được: contract test + example test xanh, TODO test đang `skipped`

**Prompt & tool declaration (CP1, CP2)**
- [ ] Chạy baseline `v0`, ghi vào `artifacts/version_log.csv`
- [ ] Liệt kê các case FAIL của `v0` và gán mỗi case một loại lỗi (`wrong_tool`, `wrong_arg_value`, `missing_info`, v.v.)
- [ ] `artifacts/system_prompt.md`: bỏ các chỉ dẫn xấu cố ý của starter (đoán thay vì hỏi, gửi không cần xác nhận, ép một bước)
- [ ] `artifacts/system_prompt.md`: thêm rule routing (khi nào `timeline` / `social_search` / `lookup` / `fetch` / `clarify`)
- [ ] `artifacts/tools.yaml`: viết lại `description` mỗi tool: làm gì, **khi nào dùng / khi nào không dùng**
- [ ] `artifacts/tools.yaml`: mô tả rõ convention args (handle không có `@`, `topic=news` cho tin tức, `timeframe`, `search_type=Top|Latest`)
- [ ] `artifacts/tools.yaml`: `send` mô tả rõ chỉ gửi khi user đã xác nhận (`confirmed=true`)
- [ ] `v1`, `v2`, `v3`: mỗi version **một** giả thuyết, metric trước/sau trong `version_log.csv`

**Tool mới (CP3)**
- [ ] `tools/<tên>/tool.py` + `TOOL.md` (frontmatter đúng contract trong `tools/README.md`)
- [ ] Đăng ký trong `tools/__init__.py` (`TOOL_FUNCTIONS`) và `artifacts/tools.yaml`
- [ ] Unit test cho tool mới trong `tests/test_tools_todo.py` (≥ 3 test)
- [ ] Ít nhất 1 eval case trong `data/eval_group.json` kiểm tra model có route tới tool mới đúng lúc

**Testing (CP3, CP4)**
- [ ] `data/eval_group.json`: case cho model (routing / args / boundary), xem Step 4
- [ ] `tests/test_tools_todo.py`: unit test cho code của tool, xem Step 4b
- [ ] `pytest`: 0 failed; 3 test của tool mới không còn `skipped` (stub của tool có sẵn được phép còn skip)

**Demo & báo cáo (CP5)**
- [ ] UI chạy được + link dùng thử
- [ ] `chat.py`: ≥ 3 lượt live, có transcript
- [ ] `report/team/group_report.md` Phần A trước 16:30, Phần B trước khi nộp
- [ ] Mỗi thành viên có `report/team/MSSV_HoTen.md`

**Bonus (tuỳ chọn)**
- [ ] `send` gửi thật lên Telegram sau khi user xác nhận, có transcript chứng minh
- [ ] Small Local Model Challenge (Step 7)
- [ ] Hơn 3 tool mới (≥ 4), mỗi tool ≥ 3 test
- [ ] Test challenge: `pytest` 0 failed, 0 skipped toàn suite

## Cấu trúc thư mục

```text
README.md, RULES.md, CHECKPOINTS.md, RUBRIC.md, SUBMISSION.md
TEAM.md                       # thông tin nhóm, thành viên, đóng góp
docs/
  TOOL-SETUP.md               # cách lấy và cấu hình API key cho từng tool
report/team/
  group_report.md             # báo cáo nhóm: Phần A (giới thiệu agent) + Phần B (bằng chứng)
  MSSV_HoTen.md               # mẫu báo cáo cá nhân, mỗi thành viên copy và đổi tên
starter_v0/
  README.md                   # file chạy, lệnh chạy, input/output, file được sửa
  agent.py                    # một lượt: model -> tool calls -> chạy tool
  chat.py                     # chat nhiều lượt, ghi transcript JSON
  run_eval.py                 # chấm routing + args, ghi runs/*.json
  versioning.py               # hash prompt/tool
  pytest.ini
  tests/
    conftest.py               # fixture offline: chặn mạng thật, fake_http, xoá env
    test_tool_contract.py     # tools.yaml <-> code <-> eval phải đồng bộ (có sẵn, giữ xanh)
    test_tools_examples.py    # ví dụ mẫu để copy
    test_tools_todo.py        # TODO CP3: challenge viết unit test cho tool
  artifacts/
    system_prompt.md          # học viên sửa
    tools.yaml                # học viên sửa
    version_log.csv           # học viên điền
  data/
    eval_base.json            # bộ eval cố định, không sửa nội dung case
    eval_group.json           # nhóm thêm 10 case (5 single + 5 multi turn)
    eval_research_extension.json
  tools/
    README.md                 # contract của folder tool
    <tool_name>/
      TOOL.md                 # frontmatter + ghi chú
      tool.py                 # code của tool
  company_policy/             # knowledge base markdown cho tool policy
  providers/                  # adapter OpenRouter/OpenAI/Anthropic/Gemini/Ollama (local)
  scripts/preflight_provider.py
  samples/                    # ví dụ format (transcript, run-analysis, version_log)
```

Báo cáo cá nhân phải đổi tên theo `MSSV_HoTen.md`, ví dụ `report/team/20241234_NguyenVanAn.md`.

## Tool Tracks

Phần mô tả dưới đây tóm tắt mỗi tool *làm gì*. Việc xác định *khi nào dùng* tool nào là phần nhóm tự định nghĩa trong prompt và tool declaration.

Core tools:

- `clarify`: gửi một câu hỏi cho người dùng và chờ lượt trả lời tiếp theo.
- `timeline`: lấy bài đăng gần đây của một tài khoản (`screenname`).
- `social_search`: tìm bài đăng theo từ khóa (`search_type`: Latest/Top).
- `lookup`: tìm trên web (có `topic` general/news và `timeframe`).
- `fetch`: đọc nội dung một URL.
- `format`: trình bày các item đã có thành markdown digest.

Optional tools (có sẵn trong starter, không tự được bonus):

- `send`: gửi text lên Telegram channel (chỉ gửi khi `confirmed=true`).
- `policy`: tìm trong company policy markdown nội bộ.
- `papers`: tìm paper trên arXiv.
- `paper_text`: tải PDF arXiv và trích text cục bộ.

Mỗi tool nằm trong thư mục riêng dưới `starter_v0/tools/<tool_name>/`.

## ⚠️ Nếu nhóm đổi tên tool: phải đồng bộ

Eval chấm theo **đúng tên tool**. Nếu nhóm đổi tên một tool cho rõ nghĩa hơn (ví dụ `send` → `send_telegram`), **phải đổi đồng bộ ở CẢ những nơi sau**, nếu không eval báo lỗi `not declared in tools.yaml` hoặc chấm sai mọi case:

1. `artifacts/tools.yaml` — field `name`
2. `tools/__init__.py` — key trong `TOOL_FUNCTIONS`
3. `data/eval_base.json` **và** `data/eval_research_extension.json` — `expect.tool_calls[].name`

(Không cần đổi tên hàm trong `tools/<folder>/tool.py` — chỉ cần key trỏ đúng hàm. Không sửa *nội dung case* trong `eval_base.json`, chỉ đổi tên tool nếu nhóm rename.)

## Setup

Chạy từ `starter_v0/`.

macOS/Linux:

```bash
cd starter_v0
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows (PowerShell):

```powershell
cd starter_v0
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Điền `.env`. Tối thiểu nên có:

```bash
OPENROUTER_API_KEY=<your-key>
TAVILY_API_KEY=<your-key>
FIRECRAWL_API_KEY=<your-key>
RAPIDAPI_KEY=<your-key>
RAPIDAPI_TWITTER_HOST=twitter-api45.p.rapidapi.com
```

Cách lấy từng key xem [docs/TOOL-SETUP.md](docs/TOOL-SETUP.md).

Preflight:

```bash
python scripts/preflight_provider.py --provider openrouter
```

Nếu preflight lỗi, sửa provider key, dependency hoặc mạng trước khi chạy eval.

## Step 1 — Chạy baseline

Chạy bộ base eval cố định với nhãn `v0`:

```bash
python run_eval.py \
  --provider openrouter \
  --version v0 \
  --suite base \
  --eval-cases data/eval_base.json
```

Kết quả lưu ở `runs/*.json`. Đọc các field:

- `summary.case_accuracy`
- `summary.tool_routing_accuracy`
- `summary.argument_accuracy`
- `summary.multiturn_accuracy`
- `results[*].result.failures`
- `results[*].result.observed_mismatch`

Run JSON cũng lưu `artifact_version`, `prompt_hash`, `tools_hash`, tool call thực tế và kết quả tool thực tế. Đó là bằng chứng cho báo cáo. Chỉ dùng run có `summary.provider_error_cases == 0` và `summary.measured_cases == summary.total_cases`.

Tùy chọn: chuyển run JSON thành bảng CSV phẳng để phân tích:

```bash
python scripts/parse_runs.py runs/ --output analysis/base_runs.csv
```

## Step 2 — Sửa một thứ

Chỉ sửa:

- `artifacts/system_prompt.md`
- `artifacts/tools.yaml`

Không sửa các case trong `data/eval_base.json`.

Học phương pháp, không học thuộc đáp án:

1. Mở run JSON. Với mỗi case FAIL, đọc `observed_mismatch` + `failures` + `actual_tool_calls`.
2. Đặt một giả thuyết: *vì sao* agent chọn sai (thiếu rule routing? thiếu convention args? prompt đang khuyến khích đoán/gửi/làm-một-bước?).
3. Sửa **một** thứ (một dòng prompt hoặc một description) để kiểm chứng giả thuyết đó.
4. Chạy lại, so metric trước/sau. Nếu không cải thiện, đổi giả thuyết.

Đổi một giả thuyết mỗi lần để version log có ý nghĩa.

## Step 3 — Chạy 3 version tối ưu

Chạy ít nhất ba version cải tiến:

```bash
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

Sau mỗi run, điền `artifacts/version_log.csv`:

```text
version,author,changed_artifact,artifact_version,prompt_hash,tools_hash,reason,hypothesis,metric_before,metric_after,run_file
```

Lấy hash và đường dẫn run file từ output của eval.

## Step 4 — Viết eval của nhóm

Viết đúng 10 case vào `data/eval_group.json`: 5 single turn (`query`) + 5 multi turn (`turns`). Ít nhất 1 case kiểm tra model có route tới tool mới của nhóm.

Mỗi case cần có:

- `id`
- `phase`: luôn là `"B"`
- `query` hoặc `turns`
- `failure_type`: một trong `wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`
- `expect`: `tool_calls` hoặc `no_tool`
- `metadata.what_it_tests`

Chạy:

```bash
python run_eval.py \
  --provider openrouter \
  --version v3 \
  --suite group \
  --eval-cases data/eval_group.json
```

Tùy chọn, chạy bộ extension:

```bash
python run_eval.py \
  --provider openrouter \
  --version v3 \
  --suite extension \
  --eval-cases data/eval_research_extension.json
```

## Step 4b — Challenge: Viết test cho tool

Eval ở Step 4 đo **model** (chọn tool và args có đúng không). Unit test ở đây đo **code của tool** (nhận args đó thì có chạy đúng không). Hai loại lỗi này khác nhau: model gọi đúng `lookup(topic="news")` nhưng tool quên gửi `topic` lên API thì eval vẫn báo PASS, còn user vẫn nhận kết quả sai.

```bash
pytest              # toàn bộ suite, offline, không tốn credit API
pytest -v tests/test_tools_todo.py
```

Có sẵn:

- `tests/test_tool_contract.py`: kiểm tra `tools.yaml` khớp với code. Mỗi tool khai báo phải có implementation, mọi param khai báo phải có trong signature hàm, có `TOOL.md` đúng tên, eval chỉ dùng tool đã khai báo. Test này phải luôn xanh, chạy lại mỗi khi rename hay thêm tool.
- `tests/test_tools_examples.py`: 5 mẫu để copy: tool local thuần, guardrail (`send` không gửi khi chưa xác nhận), mock HTTP cho tool gọi API, nhánh lỗi (thiếu key, HTTP 429), và test vòng lặp agent bằng fake provider không cần model.
- `tests/conftest.py`: mọi HTTP thật đều bị chặn, phải mock bằng fixture `fake_http`. Các env key bị xoá trước mỗi test.

Nhiệm vụ:

1. **Bắt buộc:** viết ≥ 3 test cho mỗi tool mới của nhóm (happy path; input xấu từ model như chuỗi rỗng, sai kiểu, ngoài enum; nhánh lỗi trả error dict chứ không raise).
2. **Challenge (bonus, xem [RUBRIC.md](RUBRIC.md)):** điền hết các stub `pytest.skip(TODO)` trong `tests/test_tools_todo.py` (clarify, format, send, lookup, fetch, timeline, social_search, policy). Đạt khi `pytest` báo **0 failed, 0 skipped**.
3. **Challenge+ (bonus, xem [RUBRIC.md](RUBRIC.md)):** nếu test phát hiện bug trong tool có sẵn, ghi lại bug đó, sửa nó, và giữ lại test đã bắt được bug (regression test). Ghi vào mục B5 của `report/team/group_report.md`. Gợi ý: thử input biên mà model hay gửi, như `limit=0`, `top_k=0`, số dạng chuỗi (`max_results="5"`), `items` thiếu `url`, rồi tự quyết định hành vi hiện tại có đúng mong đợi không.

Nguyên tắc: một test kiểm tra một hành vi, tên test mô tả hành vi đó (`test_send_without_confirmation_does_not_call_network`), và assert cả **request gửi đi** lẫn **kết quả trả về**.

## Step 5 — Chat live

`chat.py` dùng để chat nhiều lượt với agent. Mỗi lượt được ghi vào `transcripts/*.transcript.json`.

```bash
python chat.py --provider openrouter --version v3
```

Thử ít nhất 3 lượt live, ví dụ:

- Một yêu cầu research bình thường.
- Một yêu cầu thiếu thông tin (không nói rõ account/URL), rồi lượt sau bổ sung.
- Một yêu cầu "đăng/gửi bản tin lên Telegram" — quan sát agent có hành động ngay hay hỏi lại trước, rồi tự quyết định hành vi nào mới đúng và sửa prompt cho khớp.

## Deploy nhanh để team khác dùng thử (khuyến nghị: Cloudflare Tunnel)

Để team cùng zone tự thử agent trong Team showdown, expose UI đang chạy local ra một link public. Cách nhanh nhất, không cần đăng ký domain hay deploy lên cloud, là **Cloudflare Tunnel** (`cloudflared`).

1. Chạy UI local trước (ví dụ Streamlit mặc định cổng `8501`):

   ```bash
   streamlit run app.py            # → http://localhost:8501
   ```

2. Cài `cloudflared`:

   ```bash
   brew install cloudflared                          # macOS
   winget install --id Cloudflare.cloudflared        # Windows (hoặc: scoop install cloudflared)
   # Linux: xem https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
   ```

   Windows: nếu báo `cloudflared not recognized`, mở terminal mới rồi chạy lại.

3. Mở tunnel trỏ vào cổng UI — lệnh trả về ngay một URL `https://<random>.trycloudflare.com`:

   ```bash
   cloudflared tunnel --url http://localhost:8501
   ```

4. Copy URL đó, dán vào mục A1 ("Link dùng thử") của `report/team/group_report.md` để team khác mở thử.

Lưu ý: link `trycloudflare.com` là tạm thời, sống theo phiên `cloudflared` (tắt lệnh là mất). Giữ lệnh chạy trong suốt buổi showdown. Nếu team deploy hẳn lên Vercel/Streamlit Cloud thì dùng link đó thay cho tunnel.

## Step 6 — Báo cáo + poster

Hoàn thành `report/team/group_report.md`. File này có 2 phần với hạn khác nhau:

- **Phần A — Giới thiệu agent** (ngắn gọn 1 trang) — **phải xong trước 16:30**, làm tài liệu phụ trợ để team khác hiểu nhanh khi demo. Chỉ cần: (1) agent làm được gì, (2) agent có những tool gì và mỗi tool làm được gì, (3) vài câu hỏi mẫu để team khác tự thử.
- **Phần B — Chi tiết / Bằng chứng** — **có thể hoàn thiện sau Team showdown để nộp bài**. Bảng đầy đủ v0–v3, failure analysis, eval cases, live chat, reflection — dựa trên log thật (run JSON, version_log).

**Format Phần A:** nộp tối thiểu bản markdown trong `group_report.md`. Khuyến khích biến Phần A thành **poster HTML/SVG 1 trang** để show trực tiếp cho team cùng zone (`report/team/poster.html` hoặc `report/team/poster.svg`) — cùng nội dung, dễ nhìn hơn. Poster là tùy chọn, không thay thế bản markdown.

Mỗi thành viên copy `report/team/MSSV_HoTen.md`, đổi tên theo MSSV và họ tên của mình (ví dụ `report/team/20241234_NguyenVanAn.md`) rồi điền phần việc, đóng góp và bằng chứng.

## Step 7 — Bonus Challenge: Small Local Model

Câu hỏi: **prompt + tool declaration nhóm vừa tối ưu cho model cloud có còn đúng khi chạy model nhỏ trên máy mình không?** Model nhỏ (3B–8B) chạy offline, không tốn tiền, dữ liệu không rời máy, nhưng gọi tool kém hơn rõ: chọn sai tool, JSON arguments lỗi, bịa tool không có, gọi lặp, hoặc trả lời luôn thay vì gọi `clarify`. Bài này đo khoảng cách đó bằng log thật rồi tìm cách thu hẹp nó.

### Setup

1. Cài [Ollama](https://ollama.com/download) (`brew install ollama` trên macOS), rồi chạy `ollama serve` (app desktop tự chạy sẵn).
2. Kéo **ít nhất 2** model hỗ trợ tool calling, có kích thước khác nhau:

   ```bash
   ollama pull qwen2.5:7b      # mặc định của provider, ~4.7 GB
   ollama pull llama3.2:3b     # nhỏ hơn, ~2 GB
   # Gợi ý khác: qwen2.5:3b, llama3.1:8b, mistral:7b
   # Model phải có tag "tools" trên https://ollama.com/search?c=tools
   ```

   Máy yếu (RAM < 16 GB): dùng model 3B. Không cần API key; provider `ollama` gọi `http://localhost:11434/v1` (đổi bằng `OLLAMA_BASE_URL` nếu dùng LM Studio / llama.cpp server).

3. Preflight:

   ```bash
   python scripts/preflight_provider.py --provider ollama --model qwen2.5:7b
   ```

### Nhiệm vụ

1. **Baseline local:** chạy base eval với prompt/tools **v3** (bản tốt nhất của nhóm), không sửa gì, trên từng model local:

   ```bash
   python run_eval.py --provider ollama --model qwen2.5:7b  --version v3-qwen7b --suite base --eval-cases data/eval_base.json
   python run_eval.py --provider ollama --model llama3.2:3b --version v3-llama3b --suite base --eval-cases data/eval_base.json
   ```

2. **Phân loại lỗi:** đọc run JSON, đếm lỗi đặc thù của model nhỏ mà model cloud không mắc:
   - `wrong_tool` / bịa tên tool không có trong `tools.yaml`
   - arguments JSON lỗi: provider giữ lại raw text trong `args._invalid_json_arguments`, nên vẫn tính là lỗi arg, không biến thành `provider_error`
   - không gọi tool (trả text thay vì tool call), hoặc gọi tool khi lẽ ra phải `clarify`
   - gọi thừa / lặp cùng một tool

3. **Tối ưu cho model nhỏ:** ít nhất **2 vòng** (`v4-local`, `v5-local`), mỗi vòng một giả thuyết, như Step 2. Hướng gợi ý (không bắt buộc):
   - Rút gọn system prompt; model nhỏ dễ "lạc" với prompt dài.
   - Viết `description` của tool ngắn, cụ thể, có ví dụ args; bớt field optional.
   - Thêm 1–2 ví dụ few-shot routing trong prompt.
   - Bỏ tool không cần cho suite đang chạy để giảm nhiễu lựa chọn.

   Có thể dùng bản prompt/tools riêng cho local qua `--system-prompt` / `--tools` (ví dụ `artifacts/system_prompt_local.md`) để không phá bản v3 của model cloud.

4. **Kiểm tra ngược:** chạy lại bản `v5-local` trên model cloud. Điểm có giảm không? Có tìm được một bản prompt dùng tốt cho cả hai không?

5. Ghi mọi run vào `artifacts/version_log.csv` (ghi rõ model trong cột `reason` hoặc `version`), và điền mục **B7** trong `report/team/group_report.md`.

Lưu ý: model local chậm hơn nhiều (vài giây đến vài chục giây mỗi case). Chạy thử 3–5 case trước bằng một file eval nhỏ nếu máy yếu. Ollama có thể bỏ qua `tool_choice="required"`, nên model local có thể không gọi tool ở case bắt buộc phải gọi; đó là một lỗi cần đo, không phải bug của harness.

**Tiêu chí đạt:** ≥ 2 model local đã chạy base eval, ≥ 2 vòng tối ưu có log, bảng so sánh cloud vs local trong báo cáo, và ít nhất một kết luận có bằng chứng về việc "cái gì giúp model nhỏ gọi tool đúng hơn".

## Nộp bài

Danh sách đầy đủ và checklist ở [SUBMISSION.md](SUBMISSION.md). Tóm tắt:

- Root: `TEAM.md`, `report/team/group_report.md`, `report/team/MSSV_HoTen.md` cho mỗi thành viên, poster nếu có.
- `starter_v0/`:
  - `artifacts/system_prompt.md`, `artifacts/tools.yaml`
  - `artifacts/version_log.csv` có ít nhất `v0`, `v1`, `v2`, `v3`
  - `data/eval_group.json` đúng 10 case (5 single + 5 multi turn)
  - `tests/` (unit test cho tool mới, `pytest` 0 failed; nếu làm challenge thì `test_tools_todo.py` không còn `skip`)
  - `runs/*.json`, `transcripts/*.transcript.json`, `analysis/*.csv` nếu có
  - code tool mới, code UI + dependency đã thêm vào `requirements.txt`
  - nếu làm Small Local Model Challenge: run JSON của model local và prompt/tools riêng cho local (nếu có)

Không nộp `.env` hay API key. Push lên GitHub rồi mỗi thành viên nộp link repo trên LMS.

## Checkpoints

Các mốc 15:00 (CP1 baseline) → 15:30 (v1 + tool mới) → 16:00 (eval nhóm + v2) → 16:30 (Team showdown) → 17:30 (v3 + báo cáo Phần B) nằm trong [CHECKPOINTS.md](CHECKPOINTS.md). Đây là checkpoint tại lớp, không phải deadline.
