"""Functions for serializing results into various export formats."""

from typing import Any
from prp.pipeline.types import ParsedSampleResults


def to_result_json(sample_results: ParsedSampleResults) -> dict[str, Any]:
    """Serialize the analysis results for a sample into json format."""

    return sample_results.model_dump(mode='json')