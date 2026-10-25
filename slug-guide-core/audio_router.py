from __future__ import annotations

from typing import Any, Dict


class AudioRouter:
    """Routes a decision into speech-friendly output."""

    def route(self, result: Dict[str, Any]) -> str:
        mode = str(result.get("mode") or "SILENCE").upper()
        message = str(result.get("message") or "").strip()

        if mode == "ALERT":
            return message or "Alert: potential hazard ahead."
        if mode == "GUIDE":
            return message or "Guidance ahead. Continue with caution."
        if mode == "ASSIST":
            return message or "Follow the assisted path."
        return "No immediate hazard detected."
