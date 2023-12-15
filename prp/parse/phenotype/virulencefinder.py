"""Functions for parsing virulencefinder result."""
import json
import logging

from ...models.phenotype import ElementType, ElementTypeResult, ElementVirulenceSubtype
from ...models.phenotype import PredictionSoftware as Software
from ...models.phenotype import VirulenceGene
from ...models.sample import MethodIndex

LOG = logging.getLogger(__name__)


def _parse_virulencefinder_vir_results(pred: str) -> ElementTypeResult:
    """Parse virulence prediction results from ARIBA."""
    results = {}
    # parse virulence finder results
    species = list(k for k in pred["virulencefinder"]["results"])
    vir_genes = []
    for key, genes in pred["virulencefinder"]["results"][species[0]].items():
        # assign element subtype
        virulence_group = key.split("_")[1]
        match virulence_group:
            case 'toxin':
                subtype = ElementVirulenceSubtype.TOXIN
            case other:
                subtype = ElementVirulenceSubtype.VIR

        # parse genes
        if not genes == "No hit found":
            for gn in genes.values():
                start_pos, end_pos = map(int, gn["position_in_ref"].split(".."))
                # Some genes doesnt have accession numbers
                accnr = None if gn['accession'] == 'NA' else gn['accession']
                gene = VirulenceGene(
                    name=gn["virulence_gene"],
                    accession=accnr,
                    identity=gn["identity"],
                    coverage=gn["coverage"],
                    sequence_name=gn['protein_function'].strip(),
                    ref_start_pos=start_pos,
                    ref_end_pos=end_pos,
                    ref_gene_length=gn["template_length"],
                    alignment_length=gn["HSP_length"],
                    ref_database="virulencefinder",
                    ref_id=gn["hit_id"],
                    element_type=ElementType.VIR,
                    element_subtype=subtype,
                )
            vir_genes.append(gene)
    return ElementTypeResult(genes=vir_genes, phenotypes={}, mutations=[])


def parse_virulencefinder_vir_pred(file: str) -> ElementTypeResult | None:
    """Parse virulencefinder virulence prediction results.

    :param file: File name
    :type file: str
    :return: Return element type if virulence was predicted else null
    :rtype: ElementTypeResult | None
    """
    LOG.info("Parsing virulencefinder virulence prediction")
    pred = json.load(file)
    if "virulencefinder" in pred:
        results: ElementTypeResult = _parse_virulencefinder_vir_results(pred)
        result = MethodIndex(
            type=ElementType.VIR, software=Software.VIRFINDER, result=results
        )
    else:
        result = None
    return result
