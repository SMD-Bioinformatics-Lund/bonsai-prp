"""Functions for serializing results into various export formats."""

from typing import Any
import logging

from pydantic import TypeAdapter
from prp.models.enums import AnalysisSoftware
from prp.pipeline.types import CdmRecord, ParsedSampleResults, CdmRecord, CdmRecords

LOG = logging.getLogger(__name__)


def to_result_json(sample_results: ParsedSampleResults) -> dict[str, Any]:
    """Serialize the analysis results for a sample into json format."""

    return sample_results.model_dump(mode='json')


def to_cdm_format(sample_results: ParsedSampleResults) -> CdmRecords:
    """Format a sample result into the output expected by CDM."""
    # list of generic parsing
    targets = ['postalignqc', 'quast', 'gambit']
    results: list[CdmRecord] = []
    for res in sample_results.analysis_results:
        if res.software not in targets:
            continue
        if res.parser_status != "parsed":
            LOG.warning(res.reason)
            continue
        results.append(
            CdmRecord(id=str(res.software), software=res.software, result=res.results.model_dump())
        )
    
    # specific rules for chewbbaca
    for res in sample_results.analysis_results:
        if res.software != AnalysisSoftware.CHEWBBACA:
            continue

        if res.parser_status != "parsed":
            LOG.warning(res.reason)
            continue

        results.append(
            CdmRecord(
                id="chewbbaca_missing_loci",
                software=res.software, 
                result={"n_missing": res.results.n_missing})
        )
    return results