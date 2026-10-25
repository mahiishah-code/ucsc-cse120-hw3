"""Reusable SlugGuide core for accessibility decision making."""

import importlib.util
from pathlib import Path

_BASE = Path(__file__).resolve().parent

for _name, _file in {
    "slug_guide_core.vision_schema": _BASE / "vision_schema.py",
    "slug_guide_core.priority_engine": _BASE / "priority_engine.py",
    "slug_guide_core.navigation": _BASE / "navigation.py",
    "slug_guide_core.audio_router": _BASE / "audio_router.py",
}.items():
    _spec = importlib.util.spec_from_file_location(_name, _file)
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    globals()[_name.rsplit(".", 1)[-1]] = getattr(_module, _name.rsplit(".", 1)[-1], _module)

PriorityEngine = globals()["priority_engine"].PriorityEngine
normalize_vision_scene = globals()["vision_schema"].normalize_vision_scene
VisionObject = globals()["vision_schema"].VisionObject
VisionHazard = globals()["vision_schema"].VisionHazard
VisionScene = globals()["vision_schema"].VisionScene
NavigationState = globals()["navigation"].NavigationState
build_navigation_instruction = globals()["navigation"].build_navigation_instruction
AudioRouter = globals()["audio_router"].AudioRouter

__all__ = [
    "PriorityEngine",
    "VisionObject",
    "VisionHazard",
    "VisionScene",
    "normalize_vision_scene",
    "NavigationState",
    "build_navigation_instruction",
    "AudioRouter",
]
