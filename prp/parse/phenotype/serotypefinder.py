"""Functions for parsing serotypefinder result."""
import logging
from typing import Any

from ...models.phenotype import ElementSerotypeSubtype, ElementType, SerotypeGene

LOG = logging.getLogger(__name__)


def parse_serotype_gene(
    info: dict[str, Any],
    subtype: ElementSerotypeSubtype = ElementSerotypeSubtype.ANTIGEN,
) -> SerotypeGene:
    """Parse serotype gene prediction results."""
    start_pos, end_pos = map(int, info["position_in_ref"].split(".."))
    # Some genes doesnt have accession numbers
    accnr = None if info["accession"] == "NA" else info["accession"]
    return SerotypeGene(
        # info
        gene_symbol=info["gene"],
        accession=accnr,
        sequence_name=info["serotype"],
        # gene classification
        element_type=ElementType.ANTIGEN,
        element_subtype=subtype,
        # position
        ref_start_pos=start_pos,
        ref_end_pos=end_pos,
        ref_gene_length=info["template_length"],
        alignment_length=info["HSP_length"],
        # prediction
        identity=info["identity"],
        coverage=info["coverage"],
    )
