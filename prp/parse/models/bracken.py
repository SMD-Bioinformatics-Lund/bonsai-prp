"""Bracken specific data models."""

from pydantic import Field

from prp.parse.core.registry import register_result_model

from .base import BaseSpeciesPrediction
from .enums import TaxLevel, AnalysisSoftware, AnalysisType


@register_result_model(AnalysisSoftware.BRACKEN, AnalysisType.SPECIES)
class BrackenSpeciesPrediction(BaseSpeciesPrediction):
    """Species prediction results."""

    taxonomy_lvl: TaxLevel = Field(..., alias="taxLevel")
    kraken_assigned_reads: int = Field(..., alias="krakenAssignedReads")
    added_reads: int = Field(..., alias="addedReads")
    fraction_total_reads: float = Field(..., alias="fractionTotalReads")
