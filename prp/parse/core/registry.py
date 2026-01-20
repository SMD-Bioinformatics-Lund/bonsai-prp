"""Parser registry."""

from dataclasses import dataclass
from typing import Any, Callable, TypeAlias
from packaging.version import Version
from prp.parse.models.enums import AnalysisSoftware, AnalysisType
from prp.parse.models.base import ParserOutput
from prp.parse.core.base import BaseParser, ParserInput


ParserClass: TypeAlias = type[BaseParser]
RegistryEntry: TypeAlias = ParserClass


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


def get_parser(software: str, *, version: str) -> RegistryEntry:
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


def resolve_parser(entry, **init_kwargs) -> Callable[..., ParserOutput]:
    if isinstance(entry, type) and issubclass(entry, BaseParser):
        return entry(**init_kwargs).parse
    if callable(entry):
        return entry
    raise TypeError(f"Unsupported registry entry: {entry!r}")


def run_parser(
    software: str | AnalysisSoftware,
    *,
    version: str,
    data: ParserInput,
    want: set[AnalysisType] | None = None,
    parser_init: dict[str, Any] | None = None,
    **parse_kwargs: Any,
) -> ParserOutput:
    if not isinstance(software, (AnalysisSoftware, str)):
        raise ValueError(f"Invalid input for 'run_parser', got {type(software)}")
    
    entry = get_parser(software, version=version)
    parse_fn = resolve_parser(entry, **(parser_init or {}))
    return parse_fn(data, want=want, **parse_kwargs)
