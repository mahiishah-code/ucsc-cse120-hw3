import importlib.util
from pathlib import Path

_BASE = Path(__file__).resolve().parent / 'slug-guide-core' / 'navigation.py'
_SPEC = importlib.util.spec_from_file_location('slug_guide_core.navigation', _BASE)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

NavigationState = _MODULE.NavigationState
build_navigation_instruction = _MODULE.build_navigation_instruction
__all__ = ['NavigationState', 'build_navigation_instruction']
