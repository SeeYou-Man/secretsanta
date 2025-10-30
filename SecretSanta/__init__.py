"""Compatibility package so `import SecretSanta` works for the test suite.

This package lazily loads the top-level `SecretSanta.py` module and re-exports
its public names so `from SecretSanta import ...` continues to work.
"""
from importlib import util
from pathlib import Path

_impl_path = Path(__file__).parent.parent / 'SecretSanta.py'
_spec = util.spec_from_file_location('SecretSanta._impl', str(_impl_path))
_impl = util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

# Re-export public names from the implementation module
for _name, _obj in vars(_impl).items():
    if not _name.startswith('_'):
        globals()[_name] = _obj

__all__ = [n for n in globals().keys() if not n.startswith('_')]
