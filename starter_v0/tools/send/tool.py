from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT


def _is_confirmed(value: Any) -> bool:
    """Only a real boolean True (or the literal string "true") counts as confirmation.

    Fix for BUG-1: the model sometimes sends confirmed="false"; a non-empty string is truthy,
    so the starter code posted the message anyway.
    """
    if isinstance(value, bool):
        return value
    return isinstance(value, str) and value.strip().lower() == "true"


def _redact(message: str, token: str | None) -> str:
    # Fix for BUG-2: requests puts the full URL (with the bot token) into HTTPError messages.
    return message.replace(token, "<redacted>") if token else message


def send_telegram(text: str = "", confirmed: bool = False) -> dict[str, Any]:
    if not _is_confirmed(confirmed):
        preview = (text or "").strip()
        return {
            "tool": "send_telegram",
            "status": "needs_confirmation",
            "message": "Only send after the user explicitly confirms.",
            # Fix for BUG-1b: pause the chat loop and ask the user instead of looping.
            "awaiting_user": True,
            "question": f"Bạn xác nhận đăng nội dung sau lên Telegram không?\n\n{preview}" if preview
            else "Bạn muốn đăng nội dung nào lên Telegram? Mình sẽ hỏi xác nhận trước khi gửi.",
            "response_type": "yes_no",
        }
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    try:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            raise RuntimeError("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env var")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=TIMEOUT)
        if response.status_code == 400:
            # Fix for BUG-3: unbalanced Markdown entities -> retry as plain text.
            response = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=TIMEOUT)
        response.raise_for_status()
        return {"tool": "send_telegram", "status": "sent"}
    except Exception as exc:
        return {"tool": "send_telegram", "error": type(exc).__name__, "message": _redact(str(exc), token)}
