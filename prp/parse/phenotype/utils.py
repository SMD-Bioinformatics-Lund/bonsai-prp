"""Shared utility functions."""
from ...models.phenotype import ElementTypeResult
from ...models.phenotype import ElementType, PhenotypeInfo


def _default_amr_phenotype() -> PhenotypeInfo:
    return PhenotypeInfo(
        type = ElementType.AMR,
        group = ElementType.AMR,
        name = ElementType.AMR,
    )


def is_prediction_result_empty(result: ElementTypeResult) -> bool:
    """Check if prediction result is emtpy.

    :param result: Prediction result
    :type result: ElementTypeResult
    :return: Retrun True if no resistance was predicted.
    :rtype: bool
    """
    n_entries = len(result.genes) + len(result.mutations)
    return n_entries == 1
