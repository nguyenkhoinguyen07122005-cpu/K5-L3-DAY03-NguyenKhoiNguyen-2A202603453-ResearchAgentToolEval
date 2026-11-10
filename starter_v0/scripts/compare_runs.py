"""Compare several run JSON files (e.g. everyone's v0) to decide the next fix from evidence.

Put each person's run JSON anywhere, e.g.:
    runs_team/khoinguyen/v0_B_base_openrouter_....json
    runs_team/songthao/v0_B_base_openrouter_....json
then:
    python scripts/compare_runs.py runs_team/ runs/ --version v0
    python scripts/compare_runs.py runs_team/ --version v0 --output analysis/v0_comparison.md

A run is labelled by its parent folder (if not `runs`) + model, so name folders after people.
Output: summary per run, PASS/FAIL matrix per case, what each run actually called on failing
cases, and failure groups ranked by how many (run, case) failures one fix would address.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

# Failure group -> (where to fix, what to change). Assigned from observed behaviour, not from case id.
GROUPS: dict[str, tuple[str, str]] = {
    "tool_on_no_tool_case": ("system_prompt.md", "Model gọi tool cho câu ngoài phạm vi/meta → tìm chỉ dẫn ép luôn gọi tool (vd 'Always … pick one tool'), thêm rule trả lời thẳng"),
    "guessed_instead_of_clarify": ("system_prompt.md", "Thiếu thông tin nhưng model đoán (gọi tool thật thay vì clarify) → bỏ chỉ dẫn 'đoán thay vì hỏi', thêm rule hỏi lại"),
    "acted_instead_of_confirm": ("system_prompt.md + tools.yaml(send)", "Hành động ghi chạy ngay (gọi send) → bỏ chỉ dẫn 'cứ gửi', rule xác nhận + description send"),
    "clarify_wrong_type": ("system_prompt.md / tools.yaml(clarify)", "Đã hỏi lại nhưng sai response_type (vd text thay vì yes_no) → nói rõ khi nào dùng yes_no"),
    "missing_parallel_call": ("system_prompt.md", "Cần ≥2 tool nhưng chỉ gọi 1 → bỏ chỉ dẫn 'một bước/một tool', cho phép gọi song song"),
    "wrong_tool": ("tools.yaml (description)", "Chọn nhầm tool → description: khi nào dùng / khi nào KHÔNG dùng"),
    "wrong_args": ("tools.yaml (parameter description)", "Đúng tool, sai args → convention trong description tham số"),
    "extra_call": ("system_prompt.md", "Gọi thừa tool → rule 'chỉ gọi tool request cần'"),
    "multiturn": ("system_prompt.md", "Lỗi carry-over/correction giữa các lượt → rule hội thoại nhiều lượt"),
    "provider_error": ("setup", "Lỗi provider/key, không phải lỗi model"),
}


def classify(item: dict[str, Any]) -> str:
    res = item["result"]
    expect = item["expect"]
    actual = res.get("actual_tool_calls") or []
    actual_names = [c["name"] for c in actual]
    expected = expect.get("tool_calls", [])
    expected_names = [c["name"] for c in expected]
    if res.get("failure_type") == "provider_error":
        return "provider_error"
    if expect.get("no_tool"):
        return "tool_on_no_tool_case"
    if "clarify" in expected_names:
        want_type = next((c.get("args", {}).get("response_type") for c in expected if c["name"] == "clarify"), None)
        if "clarify" not in actual_names:
            return "acted_instead_of_confirm" if want_type == "yes_no" else "guessed_instead_of_clarify"
        return "clarify_wrong_type" if res.get("observed_mismatch") == "wrong_arg_value" else "extra_call"
    if len(expected_names) >= 2 and len(set(actual_names) & set(expected_names)) < len(set(expected_names)) and len(actual_names) < len(expected_names):
        return "missing_parallel_call"
    if item.get("is_multiturn"):
        return "multiturn"
    mismatch = res.get("observed_mismatch")
    if mismatch == "wrong_arg_value":
        return "wrong_args"
    if mismatch == "extra_tool_call":
        return "extra_call"
    return "wrong_tool"


def label_for(path: Path, run: dict[str, Any]) -> str:
    owner = path.parent.name if path.parent.name not in {"runs", "."} else ""
    model = str(run.get("model") or run.get("provider")).split("/")[-1]
    stamp = run.get("generated_at", "")[11:16]
    return f"{owner}:{model}" if owner else f"{model}@{stamp}"


def calls_text(calls: list[dict[str, Any]]) -> str:
    if not calls:
        return "(không gọi tool)"
    return "; ".join(f"{c['name']}({json.dumps(c.get('args', {}), ensure_ascii=False, sort_keys=True)})" for c in calls)


def cell(text: str, limit: int = 120) -> str:
    text = " ".join(str(text).split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--version", default="v0", help="Only runs with this version label ('all' = every version).")
    parser.add_argument("--suite", default="base")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    files: list[Path] = []
    for path in args.paths:
        files += sorted(path.rglob("*.json")) if path.is_dir() else [path]
    runs: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for file in files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "results" not in data or data.get("suite") != args.suite:
            continue
        if args.version not in {"", "all"} and data.get("version") != args.version:
            continue
        if data.get("run_id") in seen:
            continue
        seen.add(data.get("run_id"))
        runs.append((label_for(file, data) if args.version not in {"", "all"} else f"{data.get('version')}:{label_for(file, data)}", data))
    if not runs:
        raise SystemExit("Không tìm thấy run nào khớp --version/--suite.")

    out: list[str] = [f"# So sánh {len(runs)} run — version `{args.version or 'all'}`, suite `{args.suite}`", ""]
    out += ["## Tổng quan", "", "| Run | Model | case_acc | routing | args | multiturn | prompt_hash | tools_hash |",
            "|---|---|---:|---:|---:|---:|---|---|"]
    for label, run in runs:
        s = run["summary"]
        out.append(f"| {label} | {run.get('model')} | {s['case_accuracy']:.2f} | {s.get('tool_routing_accuracy', 0):.2f} | "
                   f"{s.get('argument_accuracy', 0):.2f} | {s.get('multiturn_accuracy') or 0:.2f} | {run['prompt_hash'][:12]} | {run['tools_hash'][:12]} |")
    hashes = {(r["prompt_hash"], r["tools_hash"]) for _, r in runs}
    if len(hashes) > 1:
        out += ["", "> ⚠️ Các run dùng prompt/tools KHÁC nhau (hash khác) — so sánh v0 chỉ công bằng khi hash giống nhau."]

    case_ids = [item["id"] for item in runs[0][1]["results"]]
    by_case: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for label, run in runs:
        for item in run["results"]:
            by_case[item["id"]].append((label, item))

    out += ["", "## Ma trận PASS/FAIL", "", "| Case | " + " | ".join(label for label, _ in runs) + " | fail/N |",
            "|---|" + "---|" * len(runs) + "---:|"]
    for case_id in case_ids:
        items = dict(by_case[case_id])
        marks, fails = [], 0
        for label, _ in runs:
            item = items.get(label)
            if item is None:
                marks.append("—")
            elif item["result"]["passed"]:
                marks.append("✅")
            else:
                fails += 1
                marks.append(f"❌ {classify(item)}")
        out.append(f"| {case_id} | " + " | ".join(marks) + f" | {fails}/{len(runs)} |")

    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    out += ["", "## Case FAIL: model đã gọi gì", "", "| Case | Run | Nhóm lỗi | Actual tool calls | Failures |", "|---|---|---|---|---|"]
    for case_id in case_ids:
        for label, item in by_case[case_id]:
            if item["result"]["passed"]:
                continue
            group = classify(item)
            groups[group].append((case_id, label))
            out.append(f"| {case_id} | {label} | {group} | {cell(calls_text(item['result'].get('actual_tool_calls') or []))} | "
                       f"{cell('; '.join(item['result'].get('failures') or []), 100)} |")

    out += ["", "## Hướng sửa xếp theo tác động (mỗi hướng = một giả thuyết cho một version)", "",
            "| # | Nhóm lỗi | Số lỗi (run×case) | Case | Sửa ở đâu | Gợi ý |", "|---:|---|---:|---|---|---|"]
    ranked = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for rank, (group, hits) in enumerate(ranked, start=1):
        where, hint = GROUPS[group]
        cases = ", ".join(sorted({case for case, _ in hits}))
        out.append(f"| {rank} | {group} | {len(hits)} | {cases} | {where} | {hint} |")
    if not ranked:
        out.append("| — | Không có case FAIL | 0 | | | |")

    text = "\n".join(out) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Saved {args.output}")
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
