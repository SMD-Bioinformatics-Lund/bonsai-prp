"""Parse results from Samtools."""

from itertools import chain
from typing import Any

from prp.io.delimited import DelimiterRow, is_nullish, normalize_row, read_delimited
from prp.parse.core.base import SingleAnalysisParser, StreamOrPath
from prp.parse.core.registry import register_parser
from prp.parse.models.enums import AnalysisSoftware, AnalysisType
from prp.parse.models.qc import ContigCoverage, SamtoolsCoverageQcResult

from .utils import safe_float, safe_int

SAMTOOLS = AnalysisSoftware.SAMTOOLS

COLUMN_MAP = {
    "#rname": "contig_name",
    "startpos": "start_pos",
    "endpos": "end_pos",
    "numreads": "n_reads",
    "covbases": "cov_bases",
    "coverage": "coverage",
    "meandepth": "mean_depth",
    "meanbaseq": "mean_base_quality",
    "meanmapq": "mean_map_quality",
}


def _normalize_qc_row(row: DelimiterRow) -> DelimiterRow:
    """Normalize qc row. Wraps normalize_row"""

    return normalize_row(
        row,
        key_fn=lambda r: r.strip(),
        val_fn=lambda v: None if is_nullish(v) else v,
        column_map=COLUMN_MAP,
    )


def _to_contig_result(row: dict[str, Any]) -> ContigCoverage:
    """Covert data to structured model."""
    return ContigCoverage(
        contig_name=row["contig_name"],
        start_pos=safe_int(row["start_pos"]),
        end_pos=safe_int(row["end_pos"]),
        n_reads=safe_int(row["n_reads"]),
        cov_bases=safe_float(row["cov_bases"]),
        coverage=safe_float(row["coverage"]),
        mean_depth=safe_float(row["mean_depth"]),
        mean_base_quality=safe_float(row["mean_base_quality"]),
        mean_map_quality=safe_float(row["mean_map_quality"]),
    )


@register_parser(SAMTOOLS)
class SamtoolsCovParser(SingleAnalysisParser):
    """Gambit core parser."""

    software = SAMTOOLS
    parser_name = "SamtoolsCovParser"
    parser_version = 1
    schema_version = 1

    analysis_type = AnalysisType.QC
    produces = {analysis_type}

    def _parse_one(
        self,
        source: StreamOrPath,
        *,
        strict: bool = True,
        **kwargs: Any,
    ) -> SamtoolsCoverageQcResult | None:
        """Parse Gambit core csv and return GambitcoreQcResult."""

        rows_iter = read_delimited(source)
        try:
            first_raw = next(rows_iter)
        except StopIteration:
            self.log_info(f"{self.software} input empty")
            return None

        required_cols = set(COLUMN_MAP)
        self.validate_columns(first_raw, required=required_cols, strict=strict)

        contigs: list[ContigCoverage] = []
        for raw_row in chain([first_raw], rows_iter):
            row = _normalize_qc_row(raw_row)
            contigs.append(_to_contig_result(row))
        return SamtoolsCoverageQcResult(contigs=contigs)
