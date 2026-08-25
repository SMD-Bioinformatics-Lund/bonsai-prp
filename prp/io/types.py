"""Shared IO types."""

from os import PathLike
from pathlib import Path
from typing import TypeAlias

# Path-ish types that are commonly accepted by open()
Pathish: TypeAlias = str | Path | PathLike[str]
