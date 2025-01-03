"""Parse for input config using parsers from this module."""

import logging
import json
from typing import Sequence

from .metadata import parse_run_info
from .qc import parse_quast_results, parse_postalignqc_results
from .species import parse_kraken_result, get_mykrobe_spp_prediction, SppMethodIndex
from .typing import (
    parse_cgmlst_results,
    parse_mlst_results,
    parse_virulencefinder_stx_typing,
    parse_serotypefinder_oh_typing,
    parse_mykrobe_lineage_results,
    parse_tbprofiler_lineage_results,
)
from .phenotype.resfinder import parse_resfinder_amr_pred, AMRMethodIndex
from .phenotype.amrfinder import parse_amrfinder_amr_pred, parse_amrfinder_vir_pred
from .phenotype.virulencefinder import parse_virulencefinder_vir_pred, VirulenceMethodIndex
from .phenotype.shigapass import parse_shigapass_pred, ShigaTypingMethodIndex
from .phenotype.emmtyper import parse_emmtyper_pred, EmmTypingMethodIndex
from .phenotype import mykrobe
from .phenotype import tbprofiler

from ..models.phenotype import ElementType
from ..models.sample import MethodIndex, QcMethodIndex, PipelineResult

OUTPUT_SCHEMA_VERSION = 1

LOG = logging.getLogger(__name__)

def _read_qc(smp_cnf) -> Sequence[QcMethodIndex]:
    """Read all qc related info"""
    qc_results = []
    if smp_cnf.quast:
        qc_results.append(parse_quast_results(smp_cnf.quast))

    if smp_cnf.postalnqc:
        qc_results.append(parse_postalignqc_results(smp_cnf.postalnqc))
    return qc_results


def _read_spp_prediction(smp_cnf) -> Sequence[SppMethodIndex]:
    """Read all species prediction results."""
    spp_results = []
    if smp_cnf.kraken:
        spp_results.append(parse_kraken_result(smp_cnf.kraken))

    # TODO refactor lineage and species to use path instead of dict as input
    if smp_cnf.mykrobe:
        raw_result = mykrobe._read_result(smp_cnf.mykrobe)
        spp_results.append(get_mykrobe_spp_prediction(raw_result))
    return spp_results


def _read_typing(smp_cnf) -> Sequence[MethodIndex | EmmTypingMethodIndex | ShigaTypingMethodIndex]:
    """Read typing all information."""
    typing_result = []
    if smp_cnf.pymlst:
        typing_result.append(parse_mlst_results(smp_cnf.pymlst))

    if smp_cnf.chewbbaca:
        # TODO add corrected_alleles to input
        typing_result.append(parse_cgmlst_results(smp_cnf.chewbbaca))

    if smp_cnf.emmtyper:
        typing_result.extend(parse_emmtyper_pred(smp_cnf.emmtyper))

    if smp_cnf.shigapass:
        typing_result.append(parse_shigapass_pred(smp_cnf.shigapass))

    # stx typing
    if smp_cnf.virulencefinder:
        tmp_virfinder_res: MethodIndex | None = parse_virulencefinder_stx_typing(smp_cnf.virulencefinder)
        if tmp_virfinder_res is not None:
            typing_result.append(tmp_virfinder_res)

    if smp_cnf.serotypefinder:
        LOG.info("Parse serotypefinder results")
        # OH typing
        tmp_serotype_res: MethodIndex | None = parse_serotypefinder_oh_typing(smp_cnf.serotypefinder)
        if tmp_serotype_res is not None:
            typing_result.append(tmp_serotype_res)

    # TODO refactor lineage and species to use path instead of dict as input
    if smp_cnf.mykrobe:
        raw_result = mykrobe._read_result(smp_cnf.mykrobe)
        lin_res: MethodIndex | None = parse_mykrobe_lineage_results(raw_result)
        if lin_res is not None:
            typing_result.append(lin_res)

    if smp_cnf.tbprofiler:
        raw_result = tbprofiler._read_result(smp_cnf.tbprofiler)
        typing_result.append(parse_tbprofiler_lineage_results(raw_result))

    return typing_result


def _read_resistance(smp_cnf) -> Sequence[AMRMethodIndex]:
    """Read resistance predictions."""
    resistance = []
    if smp_cnf.resfinder:
        with smp_cnf.resfinder.open("r", encoding="utf-8") as resfinder_json:
            pred_res = json.load(resfinder_json)
            for method in [ElementType.AMR, ElementType.STRESS]:
                resistance.append(parse_resfinder_amr_pred(pred_res, method))

    if smp_cnf.amrfinder:
        for method in [ElementType.AMR, ElementType.STRESS]:
            resistance.append(parse_amrfinder_amr_pred(smp_cnf.amrfinder, method))

    if smp_cnf.mykrobe:
        tmp_res = mykrobe.parse_mykrobe_amr_pred(smp_cnf.mykrobe, smp_cnf.sample_id)
        if tmp_res is not None:
            resistance.append(tmp_res)

    if smp_cnf.tbprofiler:
        # store pipeline version
        resistance.append(
            tbprofiler.parse_tbprofiler_amr_pred(smp_cnf.tbprofiler)
        )
    return resistance


def _read_virulence(smp_cnf) -> Sequence[VirulenceMethodIndex]:
    """Read virulence results."""
    virulence = []
    if smp_cnf.amrfinder:
        virulence.append(parse_amrfinder_vir_pred(smp_cnf.amrfinder))

    if smp_cnf.virulencefinder:
        # virulence genes
        raw_res: VirulenceMethodIndex | None = parse_virulencefinder_vir_pred(
            smp_cnf.virulencefinder
        )
        if raw_res is not None:
            virulence.append(raw_res)
    return virulence


def parse_sample(smp_cnf) -> PipelineResult:
    """Parse sample config object into a combined result object."""
    sample_info, seq_info, pipeline_info = parse_run_info(
        smp_cnf.nextflow_run_info, smp_cnf.process_metadata
    )
    results = {
        "sequencing": seq_info,
        "pipeline": pipeline_info,
        "qc": _read_qc(smp_cnf),
        "species_prediction": _read_spp_prediction(smp_cnf),
        "typing_result": _read_typing(smp_cnf),
        "element_type_result": [],
        **sample_info,  # add sample_name & lims_id
    }
    # read versions of softwares
    if smp_cnf.mykrobe:
        results["pipeline"].softwares.append(mykrobe.get_version(smp_cnf.mykrobe))
    if smp_cnf.tbprofiler:
        results["pipeline"].softwares.extend(tbprofiler.get_version(smp_cnf.tbprofiler))

    # add amr and virulence
    results["element_type_result"].extend(
        [*_read_resistance(smp_cnf), *_read_virulence(smp_cnf)]
    )

    # verify data consistancy
    return PipelineResult(
        sample_id=smp_cnf.sample_id, schema_version=OUTPUT_SCHEMA_VERSION, **results
    )
