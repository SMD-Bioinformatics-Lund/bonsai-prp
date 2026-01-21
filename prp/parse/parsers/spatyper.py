"""Parse spaTyper results."""

from typing import Any

from prp.io.delimited import DelimiterRow, is_nullish, normalize_row, read_delimited
from prp.parse.core.base import StreamOrPath, SingleAnalysisParser, warn_if_extra_rows
from prp.parse.core.registry import register_parser
from prp.parse.models.enums import AnalysisSoftware, AnalysisType
from prp.parse.models.typing import TypingResultSpatyper

SPATYPER = AnalysisSoftware.SPATYPER

REQUIRED_COLUMNS: set[str] = {"Sequence name", "Repeats", "Type"}
COLUMN_MAP = {
    "Sequence name": "sequence_name",
    "Repeats": "repeats",
    "Type": "type",
}


def _normalize_spatyper_row(row: DelimiterRow) -> DelimiterRow:
    """Wrapps normalize row."""
    return normalize_row(
        row,
        key_fn=lambda r: r.strip(),
        val_fn=lambda v: None if is_nullish(v) else v,
        column_map=COLUMN_MAP,
    )


def _to_typing_result(row: dict[str, Any]) -> TypingResultSpatyper:
    """Convert and validate row into Spatyper result object."""
    repeats = row.get("repeats")  # possibly split repeats on '-'
    return TypingResultSpatyper(
        sequence_name=row["sequence_name"],
        repeats=repeats,
        type=row["type"],
    )


@register_parser(SPATYPER)
class SpatyperParser(SingleAnalysisParser):
    """Parser for ShigaType results."""

    software = SPATYPER
    parser_name = "SpatyperParser"
    parser_version = 1
    schema_version = 1

    analysis_type = AnalysisType.SPATYPE
    produces = {analysis_type}

    def _parse_one(
        self,
        source: StreamOrPath,
        *,
        strict_columns: bool = False,
        strict: bool = False,
        **kwargs: Any,
    ) -> TypingResultSpatyper | None:
        """Parse shigapass predictions and return a ShigaTypingMethodIndex."""
        rows = read_delimited(source)

        try:
            first_raw = next(rows)
        except StopIteration:
            self.log_info(f"{self.software} input empty")
            return None

        self.validate_columns(
            first_raw, required=REQUIRED_COLUMNS, strict=strict_columns
        )
        first = _normalize_spatyper_row(first_raw)
        warn_if_extra_rows(
            rows, self.log_warning, context=f"{self.software} file", max_consume=10
        )

        # Build typing result
        return _to_typing_result(first)
