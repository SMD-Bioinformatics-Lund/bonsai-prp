"""Base parser functionality."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from logging import Logger, getLogger
from pathlib import Path
from typing import IO, Any, Mapping, Type, TypeAlias, TypeVar

from prp.io.delimited import validate_fields
from prp.parse.core.envelope import (
    default_empty_predicate,
    envelope_absent,
    envelope_skipped,
    run_as_envelope,
)
from prp.parse.models.base import ParserOutput, ResultEnvelope
from prp.parse.models.enums import AnalysisType, ResultStatus

ParserInput: TypeAlias = IO[bytes] | IO[str] | str | Path
ParseImplOut: TypeAlias = Mapping[AnalysisType, Any]
T = TypeVar("T")


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
        want: set[AnalysisType] | AnalysisType | None = None,
        **kwargs: Any,
    ) -> ParserOutput:
        want: set[AnalysisType] = self._normalize_want(want)

        out = self._new_output()

        # prepopulate with result envelopes for what this parser can produce
        for atype in self.produces:
            if want is not None and atype not in want:
                out.results[atype] = envelope_skipped()
            else:
                # The specific parser implementation will have to clarify why a analysis was absent
                out.results[atype] = envelope_absent(reason="Prepopulated")

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

    def _normalize_want(
        self, want: set[AnalysisType] | AnalysisType | None
    ) -> set[AnalysisType]:
        want = want or set(self.produces)
        return {want} if isinstance(want, AnalysisType) else want

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
            raise TypeError(
                f"{cls.__name__}.produces must contain exactly one AnalysisType"
            )

    @property
    def analysis_type(self) -> AnalysisType:
        """Get analysis type from what the parser produce."""
        return next(iter(self.produces))

    def empty_predicate(self) -> Callable[[Any], bool]:
        """Allow subclasses to override how "empty" is determined."""
        return default_empty_predicate

    def absent_predicate(self) -> Callable[[Any], bool] | None:
        """Optional hook if a subclass prefers a value-based absent detection instead of raising AbsentResultError."""
        return None

    def _parse_impl(
        self, source: ParserInput, *, want: set[AnalysisType], **kwargs: Any
    ) -> Mapping[str, Any]:
        env = run_as_envelope(
            analysis_name=self.analysis_type,
            fn=lambda: self._parse_one(source, **kwargs),
            empty_predicate=self.empty_predicate(),
            absent_predicate=self.absent_predicate(),
            reason_if_absent=f"{self.analysis_type} not present",
            reason_if_empty="No findings",
            meta={"parser": self.parser_name, "software": self.software},
            logger=self.logger,
        )
        return {self.analysis_type: env}

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


def parse_child(
    parser: BaseParser, source: ParserInput, atype: AnalysisType, *, strict: bool
) -> Any:
    """Utility to call another parser inside a parser."""

    child = parser.parse(source, want={atype}, strict=strict)
    env = child.results.get(atype)
    if env and isinstance(env, ResultEnvelope) and env.status == ResultStatus.PARSED:
        return env.value
    return None
