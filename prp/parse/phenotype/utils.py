"""Shared utility functions."""
from ...models.phenotype import ElementTypeResult, ResistanceGene


def _default_resistance() -> ElementTypeResult:
    gene = ResistanceGene(
        name=None,
        virulence_category=None,
        accession=None,
        depth=None,
        identity=None,
        coverage=None,
        ref_start_pos=None,
        ref_end_pos=None,
        ref_gene_length=None,
        alignment_length=None,
        ref_database=None,
        phenotypes=[],
        ref_id=None,
        contig_id=None,
        sequence_name=None,
        ass_start_pos=None,
        ass_end_pos=None,
        strand=None,
        element_type=None,
        element_subtype=None,
        target_length=None,
        res_class=None,
        res_subclass=None,
        method=None,
        close_seq_name=None,
    )
    genes = [
        gene,
    ]
    return ElementTypeResult(phenotypes=[], genes=genes, mutations=[])


def _default_variant() -> ElementTypeResult:
    mutation = ResistanceGene(
        variant_type=None,
        genes=None,
        phenotypes=[],
        position=None,
        ref_nt=None,
        alt_nt=None,
        depth=None,
    )
    mutations = [mutation]
    return ElementTypeResult(phenotypes=[], genes=[], mutations=mutations)


def is_prediction_result_empty(result: ElementTypeResult) -> bool:
    """Check if prediction result is emtpy.

    :param result: Prediction result
    :type result: ElementTypeResult
    :return: Retrun True if no resistance was predicted.
    :rtype: bool
    """
    n_entries = len(result.genes) + len(result.mutations)
    return n_entries == 1
