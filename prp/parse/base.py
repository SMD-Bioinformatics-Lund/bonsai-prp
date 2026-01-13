"""Base parser functionality."""

from abc import ABC, abstractmethod
from pathlib import Path
from logging import Logger, getLogger
from typing import Any, Mapping, Type, IO, TypeAlias
from prp.io.delimited import validate_fields
from prp.models.base import ParserOutput, AnalysisType


ParserInput: TypeAlias = IO[bytes] | IO[str] | str | Path
ParseImplOut: TypeAlias = Mapping[AnalysisType, Any]


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

    def _normalize_want(self, want: set[AnalysisType] | None) -> set[AnalysisType]:
        return want or set(self.produces)

    def _new_output(self) -> ParserOutput:
        """Create a new output model."""
        return ParserOutput(
            software=self.software,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
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
    analysis_type: AnalysisType  # subclasses set this

    def _parse_impl(self, source: ParserInput, *, want: set[AnalysisType], **kwargs: Any) -> Mapping[str, Any]:
        if self.analysis_type not in want:
            return {}
        value = self._parse_one(source, **kwargs)
        return {self.analysis_type: value} if value is not None else {}

    @abstractmethod
    def _parse_one(self, source: ParserInput, **kwargs: Any) -> Any:
        ...


ParserClass = Type[BaseParser]
