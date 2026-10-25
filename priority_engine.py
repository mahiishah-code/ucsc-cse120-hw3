import importlib.util
import sys
import types
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_PACKAGE_DIR = _BASE / 'slug-guide-core'
_PACKAGE_NAME = 'slug_guide_core'

if _PACKAGE_NAME not in sys.modules:
    package = types.ModuleType(_PACKAGE_NAME)
    package.__path__ = [str(_PACKAGE_DIR)]
    sys.modules[_PACKAGE_NAME] = package

_SPEC = importlib.util.spec_from_file_location(
    f'{_PACKAGE_NAME}.priority_engine',
    _PACKAGE_DIR / 'priority_engine.py',
    submodule_search_locations=[str(_PACKAGE_DIR)],
)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

PriorityEngine = _MODULE.PriorityEngine
__all__ = ['PriorityEngine']
