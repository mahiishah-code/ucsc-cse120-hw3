from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

_BASE = Path(__file__).resolve().parent / "vision_schema.py"
_SPEC = importlib.util.spec_from_file_location("slug_guide_core.vision_schema", _BASE)
_VISION_SCHEMA = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _VISION_SCHEMA
_SPEC.loader.exec_module(_VISION_SCHEMA)
VisionScene = _VISION_SCHEMA.VisionScene
normalize_vision_scene = _VISION_SCHEMA.normalize_vision_scene


class PriorityEngine:
    """Turns a multimodal vision scene into an accessibility decision."""

    def __init__(self, cooldown_seconds: float = 20.0):
        self.cooldown_seconds = cooldown_seconds
        self._last_signatures: Dict[str, float] = {}

    def _signature(self, hazard: Dict[str, Any]) -> str:
        label = str(hazard.get("label") or "hazard").lower()
        direction = str(hazard.get("direction") or "center").lower()
        distance = str(hazard.get("distance") or "unknown").lower()
        severity = str(hazard.get("severity") or "medium").lower()
        return f"{label}|{direction}|{distance}|{severity}"

    def _duplicate_suppressed(self, hazard: Dict[str, Any]) -> bool:
        sig = self._signature(hazard)
        now = time.time()
        last = self._last_signatures.get(sig)
        if last is not None and (now - last) < self.cooldown_seconds:
            return True
        self._last_signatures[sig] = now
        return False

    def _severity_rank(self, severity: str) -> int:
        value = (severity or "medium").lower()
        if value in {"critical", "high"}:
            return 3
        if value in {"medium", "moderate"}:
            return 2
        return 1

    def decide(self, scene: Dict[str, Any] | VisionScene) -> Dict[str, Any]:
        vision = scene if isinstance(scene, VisionScene) else normalize_vision_scene(scene)
        hazards: List[Dict[str, Any]] = [h.to_dict() for h in vision.hazards]
        objects: List[Dict[str, Any]] = [o.to_dict() for o in vision.objects]

        if hazards:
            preferred = max(hazards, key=lambda h: self._severity_rank(str(h.get("severity") or "medium")))
            rank = self._severity_rank(str(preferred.get("severity") or "medium"))
            mode = "ALERT" if rank >= 3 else "GUIDE"
            message = str(vision.message or preferred.get("message") or f"{preferred.get('label', 'Hazard')} detected.")
            if self._duplicate_suppressed(preferred):
                return {
                    "mode": "SILENCE",
                    "tier": 3,
                    "object": preferred.get("label", "scene"),
                    "hazard": False,
                    "direction": preferred.get("direction", "center"),
                    "distance": preferred.get("distance", "unknown"),
                    "message": "No new hazard notification.",
                    "confidence": preferred.get("confidence", 0.5),
                    "cooldown": self.cooldown_seconds,
                    "suppressed": True,
                    "navigation_relevant": True,
                }

            return {
                "mode": mode,
                "tier": 1 if mode == "ALERT" else 2,
                "object": preferred.get("label", "hazard"),
                "hazard": True,
                "direction": preferred.get("direction", "center"),
                "distance": preferred.get("distance", "unknown"),
                "message": message,
                "confidence": preferred.get("confidence", 0.5),
                "cooldown": self.cooldown_seconds,
                "suppressed": False,
                "navigation_relevant": True,
            }

        if objects:
            focus = objects[0]
            label = str(focus.get("label") or "scene")
            instruction = f"A {label} is nearby."
            if focus.get("hazard"):
                return {
                    "mode": "GUIDE",
                    "tier": 2,
                    "object": label,
                    "hazard": True,
                    "direction": str(focus.get("direction") or "center"),
                    "distance": str(focus.get("distance") or "unknown"),
                    "message": instruction,
                    "confidence": float(focus.get("confidence", 0.5) or 0.5),
                    "cooldown": self.cooldown_seconds,
                    "suppressed": False,
                    "navigation_relevant": True,
                }
            return {
                "mode": "ASSIST",
                "tier": 3,
                "object": label,
                "hazard": False,
                "direction": str(focus.get("direction") or "center"),
                "distance": str(focus.get("distance") or "unknown"),
                "message": "Scene is stable. Continue along the current path.",
                "confidence": float(focus.get("confidence", 0.5) or 0.5),
                "cooldown": self.cooldown_seconds,
                "suppressed": False,
                "navigation_relevant": False,
            }

        return {
            "mode": "SILENCE",
            "tier": 3,
            "object": "open pathway",
            "hazard": False,
            "direction": "none",
            "distance": "unknown",
            "message": "No immediate hazard detected.",
            "confidence": 0.7,
            "cooldown": self.cooldown_seconds,
            "suppressed": False,
            "navigation_relevant": False,
        }
