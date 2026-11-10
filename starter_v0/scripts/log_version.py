"""Append (or replace) one row of artifacts/version_log.csv from a REAL run JSON.

Each version owner runs their eval, then:

    python scripts/log_version.py runs/v1_B_base_openrouter_....json --author "Tên bạn" \
        --changed system_prompt.md \
        --reason "Bỏ câu 'single step / pick one tool'" \
        --hypothesis "R08, R13, R14 fail vì prompt ép đúng 1 tool"

- artifact_version / hashes / metric_after are read from the run JSON (never typed by hand).
- metric_before = metric_after of the previous base-suite row already in the log.
- Re-running for the same version label replaces that row instead of duplicating it.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "artifacts" / "version_log.csv"
FIELDS = ["version", "author", "changed_artifact", "artifact_version", "prompt_hash", "tools_hash",
          "reason", "hypothesis", "metric_before", "metric_after", "run_file"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    parser.add_argument("--author", required=True)
    parser.add_argument("--changed", required=True, help="changed artifact, e.g. system_prompt.md / tools.yaml / baseline")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--label", default=None, help="Row label (default: version from the run JSON, plus -<suite> if not base)")
    args = parser.parse_args()

    run_path = args.run if args.run.is_absolute() else (Path.cwd() / args.run)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    label = args.label or (run["version"] if run["suite"] == "base" else f"{run['version']}-{run['suite']}")

    rows: list[dict[str, str]] = []
    if LOG.exists():
        with LOG.open(encoding="utf-8") as file:
            rows = [row for row in csv.DictReader(file) if row.get("version")]
    index = next((i for i, row in enumerate(rows) if row["version"] == label), len(rows))  # replace in place

    before = ""
    if run["suite"] == "base":
        previous = [row for row in rows[:index] if "-" not in row["version"] and row.get("metric_after")]
        before = previous[-1]["metric_after"] if previous else ""

    try:
        rel = str(run_path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(run_path)
    new_row = {
        "version": label,
        "author": args.author,
        "changed_artifact": args.changed,
        "artifact_version": run["artifact_version"],
        "prompt_hash": run["prompt_hash"][:12],
        "tools_hash": run["tools_hash"][:12],
        "reason": args.reason,
        "hypothesis": args.hypothesis,
        "metric_before": before,
        "metric_after": f"{run['summary']['case_accuracy']:.4f}",
        "run_file": rel,
    }
    rows[index:index + 1] = [new_row]
    with LOG.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    s = run["summary"]
    print(f"{label}: case_accuracy {before or '—'} -> {s['case_accuracy']:.4f} "
          f"(routing {s.get('tool_routing_accuracy')}, args {s.get('argument_accuracy')}, multiturn {s.get('multiturn_accuracy')})")
    print(f"Updated {LOG}")


if __name__ == "__main__":
    main()
