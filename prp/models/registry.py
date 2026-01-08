"""Models related to parser registry."""

from pydantic import BaseModel
from packaging.version import Version
from typing import Callable


class VersionRange(BaseModel):
    """Associate a parser function with given software versions."""

    min_version: Version
    max_version: Version
    parser: Callable