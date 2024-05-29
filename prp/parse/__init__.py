"""Parse output of softwares in pipeline."""

from .phenotype import (
    parse_amrfinder_amr_pred,
    parse_amrfinder_vir_pred,
    parse_mykrobe_amr_pred,
    parse_resfinder_amr_pred,
    parse_shigapass_pred,
    parse_tbprofiler_amr_pred,
    parse_virulencefinder_vir_pred,
)
from .qc import parse_alignment_results, parse_postalignqc_results, parse_quast_results
from .species import parse_kraken_result
from .typing import (
    parse_cgmlst_results,
    parse_mlst_results,
    parse_mykrobe_lineage_results,
    parse_serotypefinder_oh_typing,
    parse_tbprofiler_lineage_results,
    parse_virulencefinder_stx_typing,
)
from .variant import load_variants
