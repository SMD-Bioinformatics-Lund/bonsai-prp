"""Base parser functionality."""

from abc import ABC, abstractmethod
from pathlib import Path
from logging import Logger, getLogger
from typing import Any, Mapping, Type, IO, TypeAlias, TypeVar
from prp.io.delimited import validate_fields
from prp.models.base import ParserOutput, AnalysisType, ResultEnvelope
from collections.abc import Iterator, Callable

from prp.models.enums import ResultStatus


ParserInput: TypeAlias = IO[bytes] | IO[str] | str | Path
ParseImplOut: TypeAlias = Mapping[AnalysisType, Any]
T = TypeVar("T")

EmptyPredicate = Callable[[Any], bool]


def default_empty_predicate(value: Any) -> bool:
    """Generic tester if result is empty."""
    if value is None:
        return True
    if value == "" or value == [] or value == {}:
        return True
    return False


def envelope_from_value(
        value: Any,
        *,
        empty_predicate: EmptyPredicate = default_empty_predicate,
        reason: str | None = None,
        meta: dict[str, Any] | None = None
    ) -> ResultEnvelope:
    """Create a PARSED/ EMPTY envelope based on the provided result."""

    status = ResultStatus.EMPTY if empty_predicate(value) else ResultStatus.PARSED
    return ResultEnvelope(status=status, value=value, reason=reason, meta=meta or {})


def envelope_error(reason: str, *, meta: dict[str, Any] | None = None) -> ResultEnvelope:
    """Create an envelope that signifies that an error occured."""
    return ResultEnvelope(status=ResultStatus.ERROR, reason=reason, meta=meta or {})


def envelope_absent(reason: str, *, meta: dict[str, Any] | None = None) -> ResultEnvelope:
    """Create an envelope that signifies that the result was absent in the input file."""
    return ResultEnvelope(status=ResultStatus.ABSENT, reason=reason, meta=meta or {})


def envelope_skipped(reason: str = "Omitted by user", *, meta: dict[str, Any] | None = None) -> ResultEnvelope:
    """Create an envelope that signifies that the result was skipped by the user."""
    return ResultEnvelope(status=ResultStatus.SKIPPED, reason=reason, meta=meta or {})


def set_parsed(out: dict[AnalysisType, ResultEnvelope], atype: AnalysisType, value: Any, *, empty_predicate=None):
    out[atype] = envelope_from_value(value, empty_predicate=empty_predicate)


def set_error(out: dict[AnalysisType, ResultEnvelope], atype: AnalysisType, reason: str):
    out[atype] = ResultEnvelope(status=ResultStatus.ERROR, reason=reason)


def set_absent(out: dict[AnalysisType, ResultEnvelope], atype: AnalysisType, reason: str | None = None):
    out[atype] = ResultEnvelope(status=ResultStatus.ABSENT, reason=reason)


class BaseParser(ABC):
    """Parser class structure."""

    software: str
    parser_name: str
    parser_version: int
    schema_version: int
    produces: set[AnalysisType]

    def __init__(self, *, logger: Logger | None = None):
        self.logger = logger or getLogger(f"bonsai_prp.parse.{self.parser_name}")

    def log_info(self, msg: str, **ctx):
        self.logger.info(msg, extra={"context": ctx})

    def log_warning(self, msg: str, **ctx):
        self.logger.warning(msg, extra={"context": ctx})

    def log_error(self, msg: str, **ctx):
        self.logger.error(msg, extra={"context": ctx})

    def parse(
        self,
        source: ParserInput,
        *,
        want: set[AnalysisType] | None = None,
        **kwargs: Any,
    ) -> ParserOutput:
        want = self._normalize_want(want)

        out = self._new_output()

        # prepopulate with result envelopes for what this parser can produce
        for atype in self.produces:
            if want is not None and atype not in want:
                out.results[atype] = ResultEnvelope(status=ResultStatus.SKIPPED, reason="Omitted by user")
            else:
                out.results[atype] = ResultEnvelope(status=ResultStatus.ABSENT)

        # exit if the parser cant produce what is requested
        requested = want & self.produces
        if not requested:
            self.log_info(
                "Skipping parse; parser cant produce requested output",
                requested=[w.value for w in want],
                produces=[p.value for p in self.produces],
            )
            return out

        self.log_info("Parsing", software=self.software, parser=self.parser_name)

        # Let the subclasses implement the core logic
        results = self._parse_impl(source, want=requested, **kwargs)

        # Merge results in a predictable structure
        out.results.update(results)
        return out

    def _normalize_want(self, want: set[AnalysisType] | AnalysisType | None) -> set[AnalysisType]:
        want = want or set(self.produces)
        return { want } if isinstance(want, AnalysisType) else want

    def _new_output(self) -> ParserOutput:
        """Create a new output model."""
        return ParserOutput(
            software=self.software,
            software_version=None,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            schema_version=getattr(self, "schema_version", 1),
            results={},
        )
    
    def validate_columns(
        self,
        row: Mapping[str, object],
        *,
        required: set[str],
        optional: set[str] | None = None,
        strict: bool = False,
        tool: str | None = None,
    ) -> None:
        """Thin wrapper of the validate_fields to setup logging."""
        try:
            validate_fields(row, required=required, optional=optional, strict=strict)
        except ValueError as exc:
            self.log_error(
                "Schema validation failed",
                software=self.software,
                tool=tool or self.software,
                required=sorted(required),
                got=sorted(row.keys()),
                strict=strict,
                error=str(exc),
            )
            raise

    @abstractmethod
    def _parse_impl(
        self,
        source: ParserInput,
        *,
        want: set[AnalysisType],
        **kwargs: Any,
    ) -> ParseImplOut:
        """Return results keyed by analysis_type."""
    

class SingleAnalysisParser(BaseParser):
    """Abtracted parser class for softwares that produces exactly one AnalysisType"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "produces") or len(cls.produces) != 1:
            raise TypeError(f"{cls.__name__}.produces must contain exactly one AnalysisType")

    @property
    def analysis_type(self) -> AnalysisType:
        """Get analysis type from what the parser produce."""
        return next(iter(self.produces))

    def _parse_impl(self, source: ParserInput, *, want: set[AnalysisType], **kwargs: Any) -> Mapping[str, Any]:
        try:
            value = self._parse_one(source, **kwargs)
        except Exception as exc:
            self.log_error("Parse failed", error=str(exc), analysis_type=self.analysis_type)
            return {self.analysis_type: envelope_error(str(exc))}

        return {self.analysis_type: envelope_from_value(value)}

    @abstractmethod
    def _parse_one(self, source: ParserInput, **kwargs: Any) -> Any:
        ...


def warn_if_extra_rows(
    rows: Iterator[T],
    warn: Callable[[str], None],
    *,
    context: str = "input",
    max_consume: int = 10,
    warn_at: int = 1,
) -> int:
    """
    Consume up to `max_consume` additional rows from an iterator and warn once
    if there is more than one row.

    Returns number of extra rows consumed (0 if none).

    - `warn_at`: warn when extra_rows reaches this number (default 1)
    - `max_consume`: hard cap to avoid exhausting huge streams
    """
    extra = 0
    for _ in rows:
        extra += 1
        if extra == warn_at:
            warn(f"{context} has multiple rows; using first row only")
        if extra >= max_consume:
            break
    return extra


ParserClass = Type[BaseParser]


def parse_child(parser: BaseParser, source: ParserInput, atype: AnalysisType, *, strict: bool) -> Any:
    """Utility to call another parser inside a parser."""

    child = parser.parse(source, want={atype}, strict=strict)
    env = child.results.get(atype)
    if env and isinstance(env, ResultEnvelope) and env.status == ResultStatus.PARSED:
        return env.value
    return None
