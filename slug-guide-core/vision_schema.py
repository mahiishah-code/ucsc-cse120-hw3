from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class VisionObject:
    label: str = "scene"
    direction: str = "center"
    distance: str = "unknown"
    hazard: bool = False
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "direction": self.direction,
            "distance": self.distance,
            "hazard": self.hazard,
            "confidence": self.confidence,
        }


@dataclass
class VisionHazard:
    label: str = "hazard"
    direction: str = "center"
    distance: str = "unknown"
    severity: str = "medium"
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "direction": self.direction,
            "distance": self.distance,
            "severity": self.severity,
            "confidence": self.confidence,
        }


@dataclass
class VisionScene:
    scene: str = "general"
    objects: List[VisionObject] = field(default_factory=list)
    hazards: List[VisionHazard] = field(default_factory=list)
    tier: int = 3
    message: str = ""
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene": self.scene,
            "objects": [obj.to_dict() for obj in self.objects],
            "hazards": [hazard.to_dict() for hazard in self.hazards],
            "tier": self.tier,
            "message": self.message,
            "confidence": self.confidence,
        }


def normalize_vision_scene(raw: Dict[str, Any] | None) -> VisionScene:
    raw = raw or {}
    objects = []
    hazards = []

    for item in raw.get("objects") or []:
        normalized = VisionObject(
            label=str(item.get("label") or "scene").lower(),
            direction=str(item.get("direction") or "center").lower(),
            distance=str(item.get("distance") or "unknown"),
            hazard=bool(item.get("hazard", False)),
            confidence=float(item.get("confidence", 0.5) or 0.5),
        )
        objects.append(normalized)

    for item in raw.get("hazards") or []:
        normalized = VisionHazard(
            label=str(item.get("label") or "hazard").lower(),
            direction=str(item.get("direction") or "center").lower(),
            distance=str(item.get("distance") or "unknown"),
            severity=str(item.get("severity") or "medium").lower(),
            confidence=float(item.get("confidence", 0.5) or 0.5),
        )
        hazards.append(normalized)

    tier = int(raw.get("tier") or 3)
    if tier < 1:
        tier = 1
    if tier > 3:
        tier = 3

    return VisionScene(
        scene=str(raw.get("scene") or "general"),
        objects=objects,
        hazards=hazards,
        tier=tier,
        message=str(raw.get("message") or ""),
        confidence=float(raw.get("confidence", 0.5) or 0.5),
    )
