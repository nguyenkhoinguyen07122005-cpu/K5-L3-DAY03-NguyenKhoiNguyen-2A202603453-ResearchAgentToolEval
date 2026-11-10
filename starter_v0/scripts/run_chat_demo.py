"""Scripted live chat: feeds a fixed list of user turns through chat.py's real tool loop.

Same provider, same loop, same transcript format as `python chat.py` — just non-interactive,
so the team gets a reproducible >= 3-turn transcript (Step 5) including:
  - a normal research request
  - a request with missing info, then the follow-up that supplies it
  - a Telegram post request (agent must ask yes/no first), then the explicit "yes"
  - a request routed to a team-added tool

    python scripts/run_chat_demo.py --provider openrouter --version v5
    python scripts/run_chat_demo.py --provider openrouter --version v5 --turns "câu 1" "câu 2"
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript  # noqa: E402
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

DEFAULT_TURNS = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tóm tắt 5 tweet mới nhất giúp mình",
    "Của Andrej Karpathy nhé",
    "Đăng tóm tắt 5 tweet đó lên Telegram giúp mình",
    "Có, mình xác nhận, đăng đi",
    "Tuần này trên Hacker News dân dev bàn gì về AI agents?",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", required=True, choices=["openrouter", "openai", "anthropic", "gemini", "ollama"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True)
    parser.add_argument("--system-prompt", type=Path, default=ROOT / "artifacts" / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ROOT / "artifacts" / "tools.yaml")
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--turns", nargs="+", default=DEFAULT_TURNS)
    parser.add_argument("--transcripts-dir", type=Path, default=ROOT / "transcripts")
    args = parser.parse_args()

    prompt_path = args.system_prompt if args.system_prompt.is_absolute() else ROOT / args.system_prompt
    tools_path = args.tools if args.tools.is_absolute() else ROOT / args.tools
    system_prompt = prompt_path.read_text(encoding="utf-8")
    openai_tools = to_openai_tools(load_tool_declarations(tools_path))
    provider = make_provider(args.provider)
    version = build_artifact_version(args.version, prompt_path, tools_path)

    transcript_id = "_".join([safe_slug(args.version), safe_slug(args.provider), datetime.now().strftime("%Y%m%dT%H%M%S%f")])
    path = args.transcripts_dir / f"{transcript_id}.transcript.json"
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(version),
        "provider": args.provider,
        "model": args.model or getattr(provider, "default_model", None),
        "system_prompt": str(prompt_path.relative_to(ROOT)) if prompt_path.is_relative_to(ROOT) else str(prompt_path),
        "tools": str(tools_path.relative_to(ROOT)) if tools_path.is_relative_to(ROOT) else str(tools_path),
        "history_window": args.history_window,
        "max_tool_rounds": args.max_tool_rounds,
        "source": "scripts/run_chat_demo.py",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    history: list[dict[str, str]] = []
    for index, user_text in enumerate(args.turns, start=1):
        print(f"\nYou> {user_text}")
        record = {"turn_index": index, "started_at": now_iso(), "user": user_text, "status": "started",
                  "assistant_text": None, "rounds": [], "tool_events": []}
        messages = [{"role": "system", "content": system_prompt}, *trim_history(history, args.history_window),
                    {"role": "user", "content": user_text}]
        try:
            result = run_model_tool_loop(provider=provider, messages=messages, tools=openai_tools,
                                         model=args.model, max_tool_rounds=args.max_tool_rounds)
            record.update(result)
            print(f"Agent> {result['assistant_text']}")
            history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": result["assistant_text"]}]
        except Exception as exc:
            record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
            print(f"ERROR> {record['error']}")
        record["ended_at"] = now_iso()
        transcript["turns"].append(record)
        write_transcript(path, transcript)

    print(f"\nTranscript saved: {path}")


if __name__ == "__main__":
    main()
