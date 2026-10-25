import importlib.util
from pathlib import Path

_BASE = Path(__file__).resolve().parent / 'slug-guide-core' / 'vision_schema.py'
_SPEC = importlib.util.spec_from_file_location('slug_guide_core.vision_schema', _BASE)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

VisionObject = _MODULE.VisionObject
VisionHazard = _MODULE.VisionHazard
VisionScene = _MODULE.VisionScene
normalize_vision_scene = _MODULE.normalize_vision_scene
__all__ = ['VisionObject', 'VisionHazard', 'VisionScene', 'normalize_vision_scene']
