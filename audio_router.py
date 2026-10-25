import importlib.util
from pathlib import Path

_BASE = Path(__file__).resolve().parent / 'slug-guide-core' / 'audio_router.py'
_SPEC = importlib.util.spec_from_file_location('slug_guide_core.audio_router', _BASE)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

AudioRouter = _MODULE.AudioRouter
__all__ = ['AudioRouter']
