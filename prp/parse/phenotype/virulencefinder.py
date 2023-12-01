"""Functions for parsing virulencefinder result."""
import json
import logging

from ...models.phenotype import ElementType, ElementTypeResult
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import VirulenceGene
from ...models.sample import MethodIndex
from .utils import _default_virulence

LOG = logging.getLogger(__name__)


def _parse_virulencefinder_vir_results(pred: str) -> ElementTypeResult:
    """Parse virulence prediction results from ARIBA."""
    results = {}
    # parse virulence finder results
    species = list(k for k in pred["virulencefinder"]["results"])
    for key, genes in pred["virulencefinder"]["results"][species[0]].items():
        virulence_category = key.split("_")[1]
        vir_genes = []
        if not genes == "No hit found":
            for gn in genes.values():
                start_pos, end_pos = map(int, gn["position_in_ref"].split(".."))
                gene = VirulenceGene(
                    name=gn["virulence_gene"],
                    virulence_category=virulence_category,
                    accession=gn["accession"],
                    depth=None,
                    identity=gn["identity"],
                    coverage=gn["coverage"],
                    ref_start_pos=start_pos,
                    ref_end_pos=end_pos,
                    ref_gene_length=gn["template_length"],
                    alignment_length=gn["HSP_length"],
                    ref_database="virulenceFinder",
                    ref_id=gn["hit_id"],
                    contig_id=None,
                    gene_symbol=None,
                    sequence_name=None,
                    ass_start_pos=int(None),
                    ass_end_pos=int(None),
                    strand=None,
                    element_type=None,
                    element_subtype=None,
                    target_length=int(None),
                    res_class=None,
                    res_subclass=None,
                    method=None,
                    close_seq_name=None,
                )
            vir_genes.append(gene)
        results[virulence_category] = vir_genes

    return ElementTypeResult(results)


def parse_virulencefinder_vir_pred(file: str) -> ElementTypeResult:
    """Parse virulencefinder virulence prediction results."""
    LOG.info("Parsing virulencefinder virulence prediction")
    pred = json.load(file)
    if "not virulencefinder" in pred:
        results: ElementTypeResult = _parse_virulencefinder_vir_results(pred)
    else:
        results: ElementTypeResult = _default_virulence()
    return MethodIndex(
        type=ElementType.VIR, software=Software.VIRFINDER, result=results
    )
