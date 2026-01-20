"""Functions for parsing emmtyper result."""

import logging
from typing import Any

import pandas as pd

from prp.parse.core.base import ParserInput, SingleAnalysisParser
from prp.parse.core.registry import register_parser

from prp.parse.models.enums import AnalysisType, AnalysisSoftware
from prp.parse.models.typing import TypingResultEmm
from prp.io.delimited import read_delimited


LOG = logging.getLogger(__name__)

EMMTYPER = AnalysisSoftware.EMMTYPER
EMM_FIELDS = [
    "sample_name",
    "cluster_count",
    "emmtype",
    "emm_like_alleles",
    "emm_cluster",
]


def _parse_emmtyper_results(info: dict[str, Any]) -> TypingResultEmm:
    """Parse emm gene prediction results."""
    emm_like_alleles = (
        info["emm_like_alleles"].split(";")
        if not pd.isna(info["emm_like_alleles"])
        else None
    )
    return TypingResultEmm(
        cluster_count=int(info["cluster_count"]),
        emmtype=info["emmtype"],
        emm_like_alleles=emm_like_alleles,
        emm_cluster=info["emm_cluster"],
    )


@register_parser(EMMTYPER)
class EmmTyperParser(SingleAnalysisParser):
    """Parse emmtyper output into a normalized ParserOutput bundle."""

    software = EMMTYPER
    parser_name = "EmmTyperParser"
    parser_version = 1
    schema_version = 1
    produces = {AnalysisType.EMM}

    def _parse_one(self, source: ParserInput, **_) -> TypingResultEmm | dict:
        """Parse emmtyper results."""
        reader = read_delimited(
            source, has_header=False, fieldnames=EMM_FIELDS, none_values=["-", ""]
        )
        emm_results = [_parse_emmtyper_results(row) for row in reader]
        return emm_results[0] if emm_results else {}
