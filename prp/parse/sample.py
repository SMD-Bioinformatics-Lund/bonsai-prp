"""Parse for input config using parsers from this module."""

import json
import logging
from typing import Sequence

from ..models.phenotype import AMRMethodIndex, ElementType
from ..models.sample import MethodIndex, PipelineResult, QcMethodIndex
from . import (
    amrfinder,
    kraken,
    mykrobe,
    resfinder,
    serotypefinder,
    tbprofiler,
    virulencefinder,
)
from .emmtyper import EmmTypingMethodIndex, parse_emm_pred
from .metadata import parse_run_info
from .qc import parse_postalignqc_results, parse_quast_results
from .shigapass import ShigaTypingMethodIndex, parse_shiga_pred
from .typing import parse_cgmlst_results, parse_mlst_results
from .virulencefinder import VirulenceMethodIndex

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


def _read_spp_prediction(smp_cnf) -> Sequence[mykrobe.SppMethodIndex]:
    """Read all species prediction results."""
    spp_results = []
    if smp_cnf.kraken:
        spp_results.append(kraken.parse_result(smp_cnf.kraken))

    if smp_cnf.mykrobe:
        spp_results.append(mykrobe.parse_spp_pred(smp_cnf.mykrobe))
    return spp_results


def _read_typing(
    smp_cnf,
) -> Sequence[MethodIndex | EmmTypingMethodIndex | ShigaTypingMethodIndex]:
    """Read typing all information."""
    typing_result = []
    if smp_cnf.pymlst:
        typing_result.append(parse_mlst_results(smp_cnf.pymlst))

    if smp_cnf.chewbbaca:
        typing_result.append(parse_cgmlst_results(smp_cnf.chewbbaca))

    if smp_cnf.emmtyper:
        typing_result.extend(parse_emm_pred(smp_cnf.emmtyper))

    if smp_cnf.shigapass:
        typing_result.append(parse_shiga_pred(smp_cnf.shigapass))

    # stx typing
    if smp_cnf.virulencefinder:
        tmp_virfinder_res: MethodIndex | None = virulencefinder.parse_stx_typing(
            smp_cnf.virulencefinder
        )
        if tmp_virfinder_res is not None:
            typing_result.append(tmp_virfinder_res)

    if smp_cnf.serotypefinder:
        LOG.info("Parse serotypefinder results")
        # OH typing
        tmp_serotype_res: MethodIndex | None = serotypefinder.parse_oh_typing(
            smp_cnf.serotypefinder
        )
        if tmp_serotype_res is not None:
            typing_result.append(tmp_serotype_res)

    if smp_cnf.mykrobe:
        lin_res: MethodIndex | None = mykrobe.parse_lineage_pred(smp_cnf.mykrobe)
        if lin_res is not None:
            typing_result.append(lin_res)

    if smp_cnf.tbprofiler:
        typing_result.append(tbprofiler.parse_lineage_pred(smp_cnf.tbprofiler))

    return typing_result


def _read_resistance(smp_cnf) -> Sequence[AMRMethodIndex]:
    """Read resistance predictions."""
    resistance = []
    if smp_cnf.resfinder:
        with smp_cnf.resfinder.open("r", encoding="utf-8") as resfinder_json:
            pred_res = json.load(resfinder_json)
            for method in [ElementType.AMR, ElementType.STRESS]:
                resistance.append(resfinder.parse_amr_pred(pred_res, method))

    if smp_cnf.amrfinder:
        for method in [ElementType.AMR, ElementType.STRESS]:
            resistance.append(amrfinder.parse_amr_pred(smp_cnf.amrfinder, method))

    if smp_cnf.mykrobe:
        tmp_res = mykrobe.parse_amr_pred(smp_cnf.mykrobe, smp_cnf.sample_id)
        if tmp_res is not None:
            resistance.append(tmp_res)

    if smp_cnf.tbprofiler:
        # store pipeline version
        resistance.append(tbprofiler.parse_amr_pred(smp_cnf.tbprofiler))
    return resistance


def _read_virulence(smp_cnf) -> Sequence[VirulenceMethodIndex]:
    """Read virulence results."""
    virulence = []
    if smp_cnf.amrfinder:
        virulence.append(amrfinder.parse_vir_pred(smp_cnf.amrfinder))

    if smp_cnf.virulencefinder:
        # virulence genes
        raw_res: VirulenceMethodIndex | None = virulencefinder.parse_virulence_pred(
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
        results["pipeline"].softwares.append(tbprofiler.get_version(smp_cnf.tbprofiler))

    # add amr and virulence
    results["element_type_result"].extend(
        [*_read_resistance(smp_cnf), *_read_virulence(smp_cnf)]
    )

    # verify data consistancy
    return PipelineResult(
        sample_id=smp_cnf.sample_id, schema_version=OUTPUT_SCHEMA_VERSION, **results
    )