"""Functions for parsing emmtyper result."""

import logging
from pathlib import Path
from typing import IO, Any

import pandas as pd

from prp.parse.base import BaseParser
from prp.parse.registry import register_parser

from prp.models.base import AnalysisType, ParserOutput
from prp.models.typing import TypingResultEmm

from .utils import read_delimited

LOG = logging.getLogger(__name__)

EMMTYPER = "emmtyper"
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
class EmmTyperParser(BaseParser):
    """Parse emmtyper output into a normalized ParserOutput bundle."""

    software = EMMTYPER
    parser_name = "EmmTyperParser"
    parser_version = "1"
    schema_version = 1
    produces = {AnalysisType.EMM}


    def parse(self, source: IO[bytes] | Path, want: set[AnalysisType] | None = None) -> ParserOutput:
            """
            Parse emmtyper results from a binary stream.

            Args:
                stream: Binary stream (e.g. FastAPI UploadFile.file).
                want: Which analysis blocks to produce. Defaults to all supported.

            Returns:
                ParserOutput where results include a typing block (emmtype).
            """
            want = want or self.produces

            out = ParserOutput(
                software=self.software,
                parser_name=self.parser_name,
                parser_version=self.parser_version,
                results={},
            )

            # If caller doesn't want typing, return empty bundle
            if AnalysisType.EMM not in want:
                return out
            
            self.log_info("Parsing EMMtyper results")
            reader = read_delimited(source, has_header=False, fieldnames=EMM_FIELDS, none_values=['-', ''])
            emm_results = [_parse_emmtyper_results(row) for row in reader]

            # append emm results else
            if emm_results:
                out.results[AnalysisType.EMM.value] = emm_results[0]
            return out
