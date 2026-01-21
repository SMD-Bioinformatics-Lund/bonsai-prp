"""Parse for input config using parsers from this module."""

import logging
import re
from typing import Any, Sequence

from prp.parse.exceptions import UnsupportedMethod
from prp.models.manifest import SampleManifest
from prp.parse.models.enums import AnalysisSoftware, AnalysisType
from .types import PipelineResult
# from prp.models.phenotype import (
#     AMRMethodIndex,
#     PredictionSoftware,
#     StressMethodIndex,
#     VirulenceMethodIndex,
# )
# from prp.models.qc import QcSoftware
# from prp.models.sample import SCHEMA_VERSION, MethodIndex, PipelineResult, QcMethodIndex
# from prp.models.species import BrackenSppIndex, MykrobeSppIndex, SppMethodIndex
# from prp.models.typing import (
#     EmmTypingMethodIndex,
#     SccmecTypingMethodIndex,
#     ShigaTypingMethodIndex,
#     SpatyperTypingMethodIndex,
#     TypingMethod,
#     TypingSoftware,
# )

from .igv import parse_igv_info
from .metadata import parse_run_info
from prp.parse import run_parser

LOG = logging.getLogger(__name__)


MYKROBE = "mykrobe"
VARIANT_RE = re.compile(
    r"(?P<gene>.+)_(?P<aa_change>.+)-(?P<dna_change>.+):"
    r"(?P<ref_depth>\d+):(?P<alt_depth>\d+):(?P<conf>\d+)$",
    re.IGNORECASE,
)
# Columns to validate against
REQUIRED_COLUMNS = {
    "sample",
    "drug",
    "susceptibility",
    "genotype_model",
    "variants",
    "species",
    "species_per_covg",
    "phylo_group",
    "phylo_group_per_covg",
    "lineage",
    "mykrobe_version",
}


def _read_qc(smp_cnf) -> Sequence[Any]:
    """Read all qc related info"""
    qc_results = []
    # if smp_cnf.quast:
    #     out = run_parser(
    #         software=AnalysisSoftware.QUAST, version="1.0.0", data=smp_cnf.quast
    #     )
    #     qc_results.append(
    #         QcMethodIndex(
    #             software=AnalysisSoftware.QUAST,
    #             result=out.results[AnalysisType.QC].value,
    #         )
    #     )

    # if smp_cnf.postalnqc:
    #     out = run_parser(
    #         software=AnalysisSoftware.POSTALIGNQC,
    #         version="1.0.0",
    #         data=smp_cnf.postalnqc,
    #     )
    #     qc_results.append(
    #         QcMethodIndex(
    #             software=AnalysisSoftware.POSTALIGNQC,
    #             result=out.results[AnalysisType.QC].value,
    #         )
    #     )

    # if smp_cnf.gambitcore:
    #     qc_results.append(parse_gambitcore_results(smp_cnf.gambitcore))

    # if smp_cnf.nanoplot:
    #     qc_results.append(parse_nanoplot_results(smp_cnf.nanoplot))

    # if smp_cnf.samtools:
    #     qc_results.append(parse_samtools_coverage_results(smp_cnf.samtools))

    return qc_results


def _read_spp_prediction(smp_cnf) -> Sequence[Any]:
    """Read all species prediction results."""
    spp_results = []
    # if smp_cnf.kraken:
    #     out = run_parser(
    #         software=AnalysisSoftware.BRACKEN, version="1.0.0", data=smp_cnf.kraken
    #     )
    #     spp_results.append(
    #         BrackenSppIndex(
    #             result=out.results["species"].value,
    #         )
    #     )

    # if smp_cnf.mykrobe:
    #     out = run_parser(
    #         software=PredictionSoftware.MYKROBE.value,
    #         version="1.0.0",
    #         data=smp_cnf.mykrobe,
    #     )
    #     spp_results.append(MykrobeSppIndex(result=out.results["species"].value))
    return spp_results


def _read_typing(
    smp_cnf,
) -> Sequence[Any]:
    """Read typing all information."""
    typing_result = []
    # if smp_cnf.mlst:
    #     out = run_parser(
    #         software=AnalysisSoftware.MLST, version="1.0.0", data=smp_cnf.mlst
    #     )
    #     if out.results["mlst"].status == "parsed":
    #         typing_result.extend(
    #             MethodIndex(
    #                 type=TypingMethod.MLST,
    #                 software=QcSoftware.MLST,
    #                 result=out.results["mlst"].value,
    #             )
    #         )

    # if smp_cnf.chewbbaca:
    #     out = run_parser(
    #         software=AnalysisSoftware.CHEWBBACA, version="1.0.0", data=smp_cnf.mlst
    #     )
    #     if out.results["cgmlst"].status == "parsed":
    #         typing_result.extend(
    #             MethodIndex(
    #                 type=TypingMethod.CGMLST,
    #                 software=QcSoftware.CHEWBBACA,
    #                 result=out.results["cgmlst"].value,
    #             )
    #         )

    # if smp_cnf.emmtyper:
    #     out = run_parser(
    #         software=AnalysisSoftware.EMMTYPER, version="1.0.0", data=smp_cnf.emmtyper
    #     )
    #     typing_result.extend(EmmTypingMethodIndex(result=out.results["emm"].value))

    # if smp_cnf.shigapass:
    #     out = run_parser(
    #         software=AnalysisSoftware.SHIGAPASS, version="1.0.0", data=smp_cnf.shigapass
    #     )
    #     typing_result.append(
    #         ShigaTypingMethodIndex(result=out.results[AnalysisType.SHIGATYPE].value)
    #     )

    # if smp_cnf.spatyper:
    #     out = run_parser(
    #         software=AnalysisSoftware.SPATYPER, version="1.0.0", data=smp_cnf.spatyper
    #     )
    #     typing_result.append(
    #         SpatyperTypingMethodIndex(result=out.results[AnalysisType.SPATYPE].value)
    #     )

    # if smp_cnf.sccmec:
    #     out = run_parser(
    #         software=AnalysisSoftware.SCCMECTYPER, version="1.0.0", data=smp_cnf.sccmec
    #     )
    #     first = out.results[AnalysisType.SCCMEC].value[0]
    #     typing_result.append(SccmecTypingMethodIndex(result=first))

    # # stx typing
    # if smp_cnf.virulencefinder:
    #     out = run_parser(
    #         software=AnalysisSoftware.VIRULENCEFINDER,
    #         version="1.0.0",
    #         data=smp_cnf.virulencefinder,
    #         want=AnalysisType.STX,
    #     )
    #     typing_result.append(
    #         MethodIndex(
    #             software=TypingSoftware.VIRULENCEFINDER,
    #             type=AnalysisType.STX,
    #             result=out.results[AnalysisType.STX].value,
    #         )
    #     )

    # if smp_cnf.serotypefinder:
    #     out = run_parser(
    #         software=AnalysisSoftware.SEROTYPEFINDER,
    #         version="1.0.0",
    #         data=smp_cnf.serotypefinder,
    #     )
    #     for atype in [AnalysisType.O_TYPE, AnalysisType.H_TYPE]:
    #         typing_result.extend(
    #             MethodIndex(
    #                 software=AnalysisSoftware.SEROTYPEFINDER,
    #                 type=atype,
    #                 result=out.results[atype].value,
    #             )
    #         )

    # if smp_cnf.mykrobe:
    #     out = run_parser(
    #         software=PredictionSoftware.MYKROBE.value,
    #         version="1.0.0",
    #         data=smp_cnf.mykrobe,
    #     )
    #     typing_result.append(
    #         MethodIndex(
    #             software=PredictionSoftware.MYKROBE.value,
    #             result=out.results["lineage"].value,
    #         )
    #     )

    # if smp_cnf.tbprofiler:
    #     out = run_parser(
    #         software=PredictionSoftware.TBPROFILER.value,
    #         version="1.0.0",
    #         data=smp_cnf.tbprofiler,
    #     )
    #     typing_result.append(
    #         MethodIndex(
    #             software=PredictionSoftware.TBPROFILER.value,
    #             result=out.results["lineage"].value,
    #         )
    #     )

    return typing_result


def _read_resistance(smp_cnf) -> Sequence[Any]:
    """Read resistance predictions."""
    resistance = []
    # if smp_cnf.resfinder:
    #     out = run_parser(
    #         software=AnalysisSoftware.RESFINDER, version="1.0.0", data=smp_cnf.resfinder
    #     )
    #     target = AnalysisType.AMR
    #     resistance.append(
    #         AMRMethodIndex(
    #             software=AnalysisSoftware.RESFINDER, result=out.results[target].value
    #         )
    #     )
    #     target = AnalysisType.STRESS
    #     resistance.append(
    #         StressMethodIndex(
    #             software=AnalysisSoftware.RESFINDER, result=out.results[target].value
    #         )
    #     )

    # if smp_cnf.amrfinder:
    #     out = run_parser(software="amrfinder", version="1.0.0", data=smp_cnf.amrfinder)

    #     target = AnalysisType.AMR
    #     if target.value in out.results:
    #         # cast as method index and append to resistance results
    #         resistance.append(
    #             AMRMethodIndex(
    #                 software=PredictionSoftware.AMRFINDER,
    #                 result=out.results[AnalysisType.AMR].value,
    #             )
    #         )

    #     target = AnalysisType.STRESS
    #     if target.value in out.results:
    #         # cast as method index and append to resistance results
    #         resistance.append(
    #             StressMethodIndex(
    #                 software=PredictionSoftware.AMRFINDER,
    #                 result=out.results[AnalysisType.STRESS].value,
    #             )
    #         )

    # if smp_cnf.mykrobe:
    #     out = run_parser(
    #         software=PredictionSoftware.MYKROBE.value,
    #         version="1.0.0",
    #         data=smp_cnf.mykrobe,
    #     )
    #     resistance.append(
    #         AMRMethodIndex(
    #             software=PredictionSoftware.MYKROBE.value,
    #             result=out.results[AnalysisType.AMR].value,
    #         )
    #     )

    # if smp_cnf.tbprofiler:
    #     out = run_parser(
    #         software=PredictionSoftware.TBPROFILER.value,
    #         version="1.0.0",
    #         data=smp_cnf.tbprofiler,
    #     )
    #     resistance.append(
    #         AMRMethodIndex(
    #             software=PredictionSoftware.TBPROFILER.value,
    #             result=out.results[AnalysisType.AMR].value,
    #         )
    #     )
    return resistance


def _read_virulence(smp_cnf) -> Sequence[Any]:
    """Read virulence results."""
    virulence = []
    # if smp_cnf.amrfinder:
    #     target = AnalysisType.VIRULENCE
    #     out = run_parser(
    #         software="amrfinder", version="1.0.0", data=smp_cnf.amrfinder, want=target
    #     )
    #     if target in out.results:
    #         # cast as method index and append to resistance results
    #         virulence.append(
    #             VirulenceMethodIndex(
    #                 software=PredictionSoftware.AMRFINDER,
    #                 result=out.results[AnalysisType.VIRULENCE].value,
    #             )
    #         )

    # if smp_cnf.virulencefinder:
    #     # virulence genes
    #     out = run_parser(
    #         software=AnalysisSoftware.VIRULENCEFINDER,
    #         version="1.0.0",
    #         data=smp_cnf.virulencefinder,
    #         want=AnalysisType.VIRULENCE,
    #     )
    #     virulence.append(
    #         VirulenceMethodIndex(
    #             software=TypingSoftware.VIRULENCEFINDER,
    #             result=out.results[AnalysisType.VIRULENCE].value,
    #         )
    #     )
    return virulence


def parse_sample(manifest: SampleManifest) -> PipelineResult:
    """Parse sample config object into a combined result object."""
    sample_info, seq_info, pipeline_info = parse_run_info(
        manifest.nextflow_run_info, manifest.software_info
    )
    results: dict[str, Any] = {
        "sequencing": seq_info,
        "pipeline": pipeline_info,
        "qc": _read_qc(manifest),
        "species_prediction": _read_spp_prediction(manifest),
        # "typing_result": _read_typing(smp_cnf),
        "element_type_result": [],
        **sample_info,  # add sample_name & lims_id
    }
    if manifest.ref_genome_sequence:
        (
            ref_genome_info,
            read_mapping,
            genome_annotation,
            filtered_variants,
        ) = parse_igv_info(
            manifest.ref_genome_sequence,
            manifest.ref_genome_annotation,
            manifest.igv_annotations,
        )
        results["reference_genome"] = ref_genome_info
        results["read_mapping"] = read_mapping
        results["genome_annotation"] = genome_annotation
        results["sv_variants"] = (
            filtered_variants["sv_variants"] if filtered_variants else None
        )
        results["indel_variants"] = (
            filtered_variants["indel_variants"] if filtered_variants else None
        )
        results["snv_variants"] = (
            filtered_variants["snv_variants"] if filtered_variants else None
        )
    # read versions of softwares
    # if smp_cnf.mykrobe:
    #     results["pipeline"].softwares.append(mykrobe.get_version(smp_cnf.mykrobe))
    # if smp_cnf.tbprofiler:
    #     results["pipeline"].softwares.append(tbprofiler.get_version(smp_cnf.tbprofiler))
    # if smp_cnf.kleborate_hamronization:
    #     with smp_cnf.kleborate_hamronization.open() as inpt:
    #         if (
    #             kleborate_version := hamronization.get_version(inpt)
    #         ) or kleborate_version is not None:
    #             results["pipeline"].softwares.append(kleborate_version)

    # add amr and virulence
    results["element_type_result"].extend(
        [*_read_resistance(manifest), *_read_virulence(manifest)]
    )

    # add kleborate results
    # this is a test of a updated way of sorting outputs into their dedicated category
    # if smp_cnf.kleborate and smp_cnf.kleborate_hamronization:
    #     with smp_cnf.kleborate_hamronization.open() as inpt:
    #         if (
    #             kleborate_version := hamronization.get_version(inpt)
    #         ) and kleborate_version is None:
    #             raise ValueError(
    #                 "Could not parse Kleborate version from hAMRonization file."
    #             )
    #     # reopen the file to get all entries
    #     with smp_cnf.kleborate_hamronization.open() as inpt:
    #         hamronization_entries = hamronization.parse_hamronization(inpt)
    #         analysis_results = kleborate.parse_kleborate_v3(
    #             path=smp_cnf.kleborate,
    #             version=kleborate_version.version,
    #             hamronization_entries=hamronization_entries,
    #         )

    #     # append the kleborate result to the individual categories in the result dict
    #     for res in analysis_results:
    #         # add new category if not previously defined
    #         if not res.target_field in results:
    #             results[res.target_field] = []
    #         results[res.target_field].append(res.data)

    # verify data consistancy
    return PipelineResult(
        sample_id=manifest.sample_id, **results
    )
