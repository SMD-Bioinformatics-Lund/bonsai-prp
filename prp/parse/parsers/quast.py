"""Parse Quast results."""

from typing import Any

from prp.io.delimited import DelimiterRow, is_nullish, normalize_row, read_delimited
from prp.parse.core.base import ParserInput, SingleAnalysisParser, warn_if_extra_rows
from prp.parse.core.registry import register_parser
from prp.parse.models.enums import AnalysisSoftware, AnalysisType
from prp.parse.models.qc import QuastQcResult

from .utils import safe_float, safe_int

QUAST = AnalysisSoftware.QUAST

REQUIRED_COLUMNS = {
    "Total length",
    "Reference length",
    "Largest contig",
    "# contigs",
    "N50",
    "NG50",
    "GC (%)",
    "Reference GC (%)",
    "Duplication ratio",
}
COLUMN_MAP = {
    "Total length": "total_length",
    "Reference length": "reference_length",
    "Largest contig": "largest_contig",
    "# contigs": "n_contigs",
    "N50": "n50",
    "NG50": "ng50",
    "GC (%)": "gc_perc",
    "Reference GC (%)": "reference_gc_perc",
    "Duplication ratio": "duplication_ratio",
}


def _to_qc_result(row: dict[str, Any]) -> QuastQcResult:
    """Cast row as quast result."""
    return QuastQcResult(
        total_length=safe_int(row["total_length"]),
        reference_length=safe_int(row["reference_length"]),
        largest_contig=safe_int(row["largest_contig"]),
        n_contigs=safe_int(row["n_contigs"]),
        n50=safe_int(row["n50"]),
        ng50=safe_int(row["ng50"]),
        assembly_gc=safe_float(row["gc_perc"]),
        reference_gc=safe_float(row["reference_gc_perc"]),
        duplication_ratio=safe_float(row["duplication_ratio"]),
    )


def _normalize_quast_row(row: DelimiterRow) -> DelimiterRow:
    """Wrapps normalize row."""
    return normalize_row(
        row,
        key_fn=lambda r: r.strip(),
        val_fn=lambda v: None if is_nullish(v) else v,
        column_map=COLUMN_MAP,
    )


@register_parser(QUAST)
class QuastParser(SingleAnalysisParser):
    """Parse Quast results."""

    software = QUAST
    parser_name = "QuastParser"
    parser_version = 1
    schema_version = 1

    analysis_type = AnalysisType.QC
    produces = {analysis_type}

    def _parse_one(
        self,
        source: ParserInput,
        *,
        strict_columns: bool = False,
        **kwargs: Any,
    ) -> QuastQcResult | None:
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
        first = _normalize_quast_row(first_raw)
        warn_if_extra_rows(
            rows, self.log_warning, context=f"{self.software} file", max_consume=10
        )

        # build qc result
        return _to_qc_result(first)
