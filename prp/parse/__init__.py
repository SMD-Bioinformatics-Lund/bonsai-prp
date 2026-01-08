"""Parse output of softwares in pipeline."""

from importlib import import_module
from pathlib import Path

from .qc import (
    parse_alignment_results,
    parse_gambitcore_results,
    parse_postalignqc_results,
    parse_quast_results,
)
from .sample import parse_sample
from .typing import parse_cgmlst_results, parse_mlst_results
from .variant import load_variants


# auto-import all modules under parse/ to ensure that all parsers are registered
_pkg_dir = Path(__file__).parent
for file in _pkg_dir.glob("*.py"):
    if file.name not in ("__init__.py", "registry.py"):
        import_module(f"{__name__}.{file.stem}")
