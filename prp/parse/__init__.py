"""Parse output of softwares in pipeline."""

from importlib import import_module
from pathlib import Path

from .core.registry import run_parser

# auto-import all modules under parse/parsers to ensure that all parsers are registered
_pkg_dir = Path(__file__).parent.joinpath("parsers")
for file in _pkg_dir.glob("*.py"):
    if file.name not in ("__init__.py", "registry.py"):
        import_module(f"{__name__}.{file.stem}")
