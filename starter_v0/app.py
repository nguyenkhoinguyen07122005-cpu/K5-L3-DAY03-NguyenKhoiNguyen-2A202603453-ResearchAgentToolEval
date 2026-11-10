"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py
Then expose it for other teams:
    cloudflared tunnel --url http://localhost:8501

Reuses the exact multi-round tool loop of chat.py (same prompt, tools, transcript format),
so every UI conversation is also logged to transcripts/*.transcript.json.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import ROOT, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
EXAMPLES = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tweet mới nhất của Andrej Karpathy là gì?",
    "Mọi người đang bàn gì về GPT-5 trên Twitter? Lấy bài top.",
    "Tóm tắt bài này giúp mình: https://www.anthropic.com/research",
    "Tuần này trên Hacker News bàn gì về Rust?",
    "Tìm 5 repo GitHub nhiều sao nhất về LLM agent framework",
    "Đăng bản tin AI hôm nay lên Telegram giúp mình",
]
TOOL_ICONS = {
    "clarify": "❓", "timeline": "👤", "social_search": "🐦", "lookup": "🌐", "fetch": "📄", "format": "📰",
    "send": "📤", "policy": "📘", "papers": "📚", "paper_text": "📑",
    "wikipedia": "📖", "hackernews": "🟧", "github_repos": "🐙", "hf_models": "🤗",
}

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")


# ---------------------------------------------------------------- state ----

def new_transcript(cfg: dict[str, Any]) -> dict[str, Any]:
    version = build_artifact_version(cfg["version"], cfg["prompt_path"], cfg["tools_path"])
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join(["ui", safe_slug(cfg["version"]), safe_slug(cfg["provider"]), stamp])
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(version),
        "provider": cfg["provider"],
        "model": cfg["model"] or None,
        "system_prompt": str(cfg["prompt_path"].relative_to(ROOT)) if cfg["prompt_path"].is_relative_to(ROOT) else str(cfg["prompt_path"]),
        "tools": str(cfg["tools_path"].relative_to(ROOT)) if cfg["tools_path"].is_relative_to(ROOT) else str(cfg["tools_path"]),
        "history_window": cfg["history_window"],
        "max_tool_rounds": cfg["max_rounds"],
        "source": "streamlit_ui",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def reset_conversation() -> None:
    for key in ("messages", "history", "transcript", "pending_input"):
        st.session_state.pop(key, None)


def needs_yes_no(turn: dict[str, Any]) -> bool:
    """True when the agent paused on a yes/no confirmation (clarify yes_no or send needs_confirmation)."""
    if turn.get("status") != "waiting_for_user" or not turn.get("tool_events"):
        return False
    result = turn["tool_events"][-1].get("result") or {}
    return result.get("response_type") == "yes_no" or result.get("status") == "needs_confirmation"


# -------------------------------------------------------------- sidebar ----

with st.sidebar:
    st.header("⚙️ Cấu hình")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model (trống = mặc định của provider)", value="")
    version_label = st.text_input("Version label", value="v5")
    prompt_path = ROOT / st.text_input("System prompt", value="artifacts/system_prompt.md")
    tools_path = ROOT / st.text_input("Tools YAML", value="artifacts/tools.yaml")
    history_window = st.slider("History window (cặp lượt)", 0, 10, 5)
    max_rounds = st.slider("Max tool rounds / lượt", 1, 6, 4)
    if st.button("🧹 Cuộc trò chuyện mới", use_container_width=True):
        reset_conversation()
        st.rerun()

cfg = {
    "provider": provider_name, "model": model.strip(), "version": version_label.strip() or "ui",
    "prompt_path": prompt_path, "tools_path": tools_path,
    "history_window": history_window, "max_rounds": max_rounds,
}

try:
    system_prompt = prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(declarations)
    artifact_version = build_artifact_version(cfg["version"], prompt_path, tools_path)
except Exception as exc:  # bad path in the sidebar
    st.error(f"Không đọc được prompt/tools: {exc}")
    st.stop()

with st.sidebar:
    st.caption(f"artifact_version: `{artifact_version.artifact_version}`")
    st.subheader(f"🧰 {len(declarations)} tool")
    for item in declarations:
        icon = TOOL_ICONS.get(item["name"], "🔧")
        first_sentence = item.get("description", "").split(". ")[0][:110]
        st.markdown(f"{icon} **{item['name']}** — {first_sentence}")

st.session_state.setdefault("messages", [])
st.session_state.setdefault("history", [])
if "transcript" not in st.session_state:
    st.session_state.transcript = new_transcript(cfg)

# ----------------------------------------------------------------- main ----

st.title("🔎 Research Agent")
st.caption("Tìm tin web, tweet theo người/chủ đề, đọc URL, paper arXiv, Wikipedia, Hacker News, GitHub, Hugging Face — "
           "hỏi lại khi thiếu thông tin và luôn xin xác nhận trước khi đăng Telegram.")

if not st.session_state.messages:
    st.markdown("**Thử nhanh:**")
    cols = st.columns(2)
    for index, example in enumerate(EXAMPLES):
        if cols[index % 2].button(example, key=f"ex{index}", use_container_width=True):
            st.session_state.pending_input = example
            st.rerun()


def render_tool_events(events: list[dict[str, Any]]) -> None:
    for event in events:
        name = event.get("tool", "?")
        result = event.get("result") or {}
        badge = "⚠️ " if isinstance(result, dict) and result.get("error") else ""
        with st.expander(f"{badge}{TOOL_ICONS.get(name, '🔧')} `{name}`({json.dumps(event.get('args', {}), ensure_ascii=False)[:120]})"):
            st.json(result, expanded=False)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("tool_events"):
            render_tool_events(message["tool_events"])
        st.markdown(message["content"])

last = st.session_state.messages[-1] if st.session_state.messages else None
if last and last["role"] == "assistant" and last.get("needs_yes_no"):
    st.info("Agent đang chờ bạn xác nhận hành động ghi (gửi Telegram).")
    yes, no = st.columns(2)
    if yes.button("✅ Có, xác nhận", use_container_width=True):
        st.session_state.pending_input = "Có, mình xác nhận."
        st.rerun()
    if no.button("❌ Không, huỷ", use_container_width=True):
        st.session_state.pending_input = "Không, đừng gửi."
        st.rerun()

user_text = st.chat_input("Hỏi agent…") or st.session_state.pop("pending_input", None)

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    transcript = st.session_state.transcript
    turn_record: dict[str, Any] = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_text},
    ]
    with st.chat_message("assistant"):
        try:
            with st.spinner("Agent đang suy nghĩ và gọi tool…"):
                provider = make_provider(provider_name)
                result = run_model_tool_loop(
                    provider=provider, messages=messages, tools=openai_tools,
                    model=cfg["model"] or None, max_tool_rounds=max_rounds,
                )
            turn_record.update(result)
            answer = result["assistant_text"] or "(không có nội dung)"
            render_tool_events(result["tool_events"])
            st.markdown(answer)
            st.session_state.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": answer}]
            st.session_state.messages.append({
                "role": "assistant", "content": answer, "tool_events": result["tool_events"],
                "needs_yes_no": needs_yes_no(result),
            })
        except Exception as exc:
            turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
            st.error(f"Lỗi provider: {type(exc).__name__}: {exc}. Kiểm tra API key trong .env.")
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {type(exc).__name__}: {exc}"})

    turn_record["ended_at"] = now_iso()
    transcript["turns"].append(turn_record)
    write_transcript(ROOT / "transcripts" / f"{transcript['transcript_id']}.transcript.json", transcript)
    st.rerun()

if st.session_state.transcript["turns"]:
    st.caption(f"Transcript: `transcripts/{st.session_state.transcript['transcript_id']}.transcript.json`")
