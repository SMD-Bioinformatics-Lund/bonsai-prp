"""Parser registry."""

from dataclasses import dataclass
from typing import Callable, TypeAlias
from packaging.version import Version
from prp.models.base import ParserOutput
from prp.parse.base import BaseParser


ParserFn: TypeAlias = Callable[..., ParserOutput]
ParserClass: TypeAlias = type[BaseParser]
RegistryEntry: TypeAlias = ParserFn | ParserClass


@dataclass(order=True, slots=True)
class VersionRange:
    """Maps a parser to an inclusive software-version interval."""

    min_version: Version
    max_version: Version
    parser: RegistryEntry


_REGISTRY: dict[str, list[VersionRange]] = {}


def register_parser(software: str, min_version: str | None = None, max_version: str | None = None):
    """Decorator to register a parser for a range of versions.
    
    Null values means either undefined or no upper range.
    """
    min_version = min_version or "0.0.0"
    max_version = max_version or "99999.0.0"

    def wrapper(cls: RegistryEntry):
        range = VersionRange(
            min_version=Version(min_version), max_version=Version(max_version), parser=cls
        )
        _REGISTRY.setdefault(software, []).append(range)
        return cls
    return wrapper


def get_parser(software: str, version: str) -> Callable:
    """Get parser from registry."""
    version = Version(version)

    if software not in registered_softwares():
        raise ValueError(f"No parser registered for software: {software}")
    
    for span in sorted(_REGISTRY[software]):
        if span.min_version <= version <= span.max_version:
            return span.parser
        
    raise ValueError(f"No parser available for software '{software}' version {version}")


def registered_softwares() -> list[str]:
    """Get registered softwares."""

    return list(_REGISTRY.keys())


def registered_version_ranges(software: str) -> list[VersionRange]:
    """Get ranges for registered software."""

    return _REGISTRY.get(software, [])
