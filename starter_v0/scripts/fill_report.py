"""Fill the evidence tables of artifacts/REPORT.md from REAL logs.

Replaces every block between `<!-- AUTO:<NAME> -->` and `<!-- /AUTO:<NAME> -->` with a table
built from runs/*.json, artifacts/version_log.csv and transcripts/*.transcript.json.
Text outside the markers (the team's own analysis) is never touched. Safe to re-run.

    python scripts/fill_report.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "artifacts" / "REPORT.md"
BASE_ORDER = ["v0", "v1", "v2", "v3", "v4", "v5"]


def cell(value: Any, limit: int = 140) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(str(text).split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def calls_text(calls: list[dict[str, Any]]) -> str:
    if not calls:
        return "(không gọi tool)"
    return "; ".join(f"{c['name']}({json.dumps(c.get('args', {}), ensure_ascii=False, sort_keys=True)})" for c in calls)


def pct(value: Any) -> str:
    return "—" if value is None else f"{float(value):.2f}"


def load_runs() -> dict[tuple[str, str], dict[str, Any]]:
    """Latest run per (version, suite)."""
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted((ROOT / "runs").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_path"] = str(path.relative_to(ROOT))
        key = (data["version"], data["suite"])
        if key not in latest or data["generated_at"] >= latest[key]["generated_at"]:
            latest[key] = data
    return latest


def load_version_log() -> list[dict[str, str]]:
    path = ROOT / "artifacts" / "version_log.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        return list(csv.DictReader(file))


def table_b1(runs, log) -> str:
    by_version = {row["version"]: row for row in log}
    lines = ["| Version | Changed Artifact | Hypothesis | Metric Before | Metric After (case_acc) | routing | args | multiturn | Run File |",
             "|---|---|---|---:|---:|---:|---:|---:|---|"]
    for version in BASE_ORDER:
        run = runs.get((version, "base"))
        row = by_version.get(version, {})
        if not run:
            continue
        s = run["summary"]
        lines.append(f"| {version} | {cell(row.get('changed_artifact', '?'))} | {cell(row.get('hypothesis', ''), 220)} | "
                     f"{row.get('metric_before') or '—'} | {pct(s['case_accuracy'])} ({s['passed_cases']}/{s['measured_cases']}) | "
                     f"{pct(s.get('tool_routing_accuracy'))} | {pct(s.get('argument_accuracy'))} | {pct(s.get('multiturn_accuracy'))} | "
                     f"`{run['_path']}` |")
    return "\n".join(lines) if len(lines) > 2 else "_Chưa có run base nào — chạy `python scripts/run_all.py`._"


def table_matrix(runs) -> str:
    versions = [v for v in BASE_ORDER if (v, "base") in runs]
    if not versions:
        return "_Chưa có run._"
    case_ids = [item["id"] for item in runs[(versions[0], "base")]["results"]]
    status = {v: {item["id"]: item["result"] for item in runs[(v, "base")]["results"]} for v in versions}
    lines = ["| Case | " + " | ".join(versions) + " |", "|---|" + "---|" * len(versions)]
    for case_id in case_ids:
        marks = []
        for v in versions:
            res = status[v].get(case_id)
            marks.append("—" if res is None else ("✅" if res["passed"] else f"❌ {res.get('observed_mismatch') or ''}"))
        lines.append(f"| {case_id} | " + " | ".join(marks) + " |")
    return "\n".join(lines)


def table_b2(runs) -> str:
    versions = [v for v in BASE_ORDER if (v, "base") in runs]
    if not versions:
        return "_Chưa có run._"
    lines = ["| Case ID | Seen in | Failure Type | Observed mismatch | Actual Tool Calls | What Failed | Fixed in |",
             "|---|---|---|---|---|---|---|"]
    reported: set[str] = set()
    for index, version in enumerate(versions):
        for item in runs[(version, "base")]["results"]:
            res = item["result"]
            if res["passed"] or item["id"] in reported:
                continue
            reported.add(item["id"])
            fixed_in = "chưa sửa"
            for later in versions[index + 1:]:
                later_res = next(r["result"] for r in runs[(later, "base")]["results"] if r["id"] == item["id"])
                if later_res["passed"]:
                    fixed_in = later
                    break
            lines.append(f"| {item['id']} | {version} | {res.get('case_failure_type')} | {res.get('observed_mismatch')} | "
                         f"{cell(calls_text(res.get('actual_tool_calls') or []), 160)} | {cell('; '.join(res.get('failures') or []), 160)} | {fixed_in} |")
    return "\n".join(lines) if len(lines) > 2 else "_Không có case FAIL._"


def table_suite(runs, suite: str) -> str:
    candidates = [data for (version, s), data in runs.items() if s == suite]
    if not candidates:
        return f"_Chưa có run suite `{suite}`._"
    run = max(candidates, key=lambda d: d["generated_at"])
    s = run["summary"]
    lines = [f"Run: `{run['_path']}` — version `{run['artifact_version']}` — case_accuracy **{pct(s['case_accuracy'])}** "
             f"({s['passed_cases']}/{s['measured_cases']}), routing {pct(s.get('tool_routing_accuracy'))}, "
             f"args {pct(s.get('argument_accuracy'))}, multiturn {pct(s.get('multiturn_accuracy'))}", "",
             "| Case ID | Turns | What It Tests | Expected Tool/Behavior | Actual Tool Calls | Result |",
             "|---|---|---|---|---|---|"]
    for item in run["results"]:
        expect = item["expect"]
        expected = "no tool" if expect.get("no_tool") else calls_text(expect.get("tool_calls", []))
        res = item["result"]
        verdict = "PASS" if res["passed"] else f"FAIL ({cell('; '.join(res.get('failures') or []), 90)})"
        lines.append(f"| {item['id']} | {'multi' if item['is_multiturn'] else 'single'} | "
                     f"{cell(item.get('metadata', {}).get('what_it_tests', ''), 120)} | {cell(expected, 120)} | "
                     f"{cell(calls_text(res.get('actual_tool_calls') or []), 120)} | {verdict} |")
    return "\n".join(lines)


def table_b4() -> str:
    paths = [p for p in (ROOT / "transcripts").glob("*.transcript.json")]
    if not paths:
        return "_Chưa có transcript — chạy `python scripts/run_chat_demo.py ...` hoặc `python chat.py ...`._"
    path = max(paths, key=lambda p: p.stat().st_mtime)
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = [f"Transcript: `{path.relative_to(ROOT)}` — `{data.get('artifact_version')}` — model `{data.get('model')}`", "",
             "| Turn | User Request | Tool Calls | Status | Agent reply (rút gọn) |", "|---|---|---|---|---|"]
    for turn in data.get("turns", []):
        calls = [{"name": e.get("tool"), "args": e.get("args", {})} for e in turn.get("tool_events", [])]
        reply = turn.get("assistant_text") or turn.get("error") or ""
        lines.append(f"| {turn['turn_index']} | {cell(turn['user'], 80)} | {cell(calls_text(calls), 150)} | "
                     f"{turn.get('status')} | {cell(reply, 160)} |")
    return "\n".join(lines)


def table_b7(runs, log) -> str:
    rows = [r for r in log if "local" in r["version"] or re.search(r"-(qwen|llama|mistral|phi|gemma)", r["version"])]
    if not rows:
        return "_Chưa chạy local model — `python scripts/run_all.py --skip-base --skip-group --skip-extension --skip-chat --local-models qwen2.5:7b llama3.2:3b`._"
    lines = ["| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |",
             "|---|---|---|---:|---:|---:|---:|---|"]
    for row in rows:
        run = json.loads((ROOT / row["run_file"]).read_text(encoding="utf-8"))
        s = run["summary"]
        lines.append(f"| {row['version']} | {run['model']} ({run['provider']}) | {row['changed_artifact']} | {pct(s['case_accuracy'])} | "
                     f"{pct(s.get('tool_routing_accuracy'))} | {pct(s.get('argument_accuracy'))} | {pct(s.get('multiturn_accuracy'))} | `{row['run_file']}` |")
    return "\n".join(lines)


def table_b7_patterns(log) -> str:
    rows = [r for r in log if "local" in r["version"] or re.search(r"-(qwen|llama|mistral|phi|gemma)", r["version"])]
    if not rows:
        return "_Chưa có run local._"
    lines = ["| Run | wrong/hallucinated tool | invalid JSON args | no tool call | missed clarify | extra/repeated calls |",
             "|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        run = json.loads((ROOT / row["run_file"]).read_text(encoding="utf-8"))
        counts = {"hallucinated": 0, "invalid_json": 0, "no_tool": 0, "missed_clarify": 0, "extra": 0}
        from tools import TOOL_FUNCTIONS  # local import: only needed here
        for item in run["results"]:
            res = item["result"]
            calls = res.get("actual_tool_calls") or []
            counts["hallucinated"] += sum(1 for c in calls if c["name"] not in TOOL_FUNCTIONS)
            counts["invalid_json"] += sum(1 for c in calls if "_invalid_json_arguments" in (c.get("args") or {}))
            if not item["expect"].get("no_tool") and not calls:
                counts["no_tool"] += 1
            expected_names = [c["name"] for c in item["expect"].get("tool_calls", [])]
            if "clarify" in expected_names and "clarify" not in [c["name"] for c in calls]:
                counts["missed_clarify"] += 1
            if len(calls) > max(1, len(expected_names)):
                counts["extra"] += 1
        lines.append(f"| {row['version']} | {counts['hallucinated']} | {counts['invalid_json']} | {counts['no_tool']} | "
                     f"{counts['missed_clarify']} | {counts['extra']} |")
    return "\n".join(lines)


def main() -> None:
    import sys

    sys.path.insert(0, str(ROOT))
    runs = load_runs()
    log = load_version_log()
    blocks = {
        "B1": table_b1(runs, log),
        "B1_MATRIX": table_matrix(runs),
        "B2": table_b2(runs),
        "B3": table_suite(runs, "group"),
        "B3_EXT": table_suite(runs, "extension"),
        "B4": table_b4(),
        "B7": table_b7(runs, log),
        "B7_PATTERNS": table_b7_patterns(log),
    }
    text = REPORT.read_text(encoding="utf-8")
    for name, content in blocks.items():
        pattern = re.compile(rf"(<!-- AUTO:{name} -->)(.*?)(<!-- /AUTO:{name} -->)", re.S)
        text, n = pattern.subn(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text)
        print(f"{name}: {'updated' if n else 'marker not found'}")
    REPORT.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
