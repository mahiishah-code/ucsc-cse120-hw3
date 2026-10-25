from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NavigationState:
    destination: str = "Engineering 2"
    direction: str = "center"
    distance_meters: int = 120
    mode: str = "idle"
    instruction: str = "Continue toward the next marked path."

    def to_dict(self):
        return {
            "destination": self.destination,
            "direction": self.direction,
            "distance_meters": self.distance_meters,
            "mode": self.mode,
            "instruction": self.instruction,
        }


def build_navigation_instruction(direction: str | None, destination: str = "Engineering 2") -> str:
    normalized = str(direction or "center").lower()
    if normalized == "left":
        return f"Turn left toward {destination}."
    if normalized == "right":
        return f"Turn right toward {destination}."
    if normalized == "none":
        return f"Path is clear. Continue steadily toward {destination}."
    return f"Continue straight toward {destination}."
