"""Functions for parsing emmtyper result."""

import logging

from typing import Any

from ...models.phenotype import ElementType, ElementVirulenceSubtype
from ...models.phenotype import (EmmtypeGene)

LOG = logging.getLogger(__name__)


def parse_emm_gene(
    info: dict[str, Any], subtype: ElementVirulenceSubtype = ElementVirulenceSubtype.VIR
) -> EmmtypeGene:
    
    emm_like_alleles = info["emm_like_alleles"].split(";")
    """Parse emm gene prediction results."""
    return EmmtypeGene(
        # info
        cluster_count=info["cluster_count"],
        emmtype=info["emmtype"],
        emm_like_alleles=emm_like_alleles,
        emm_cluster=info["emm_cluster"],
        # gene classification
        element_type=ElementType.VIR,
        element_subtype=subtype,
    )
