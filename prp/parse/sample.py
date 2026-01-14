"""Parse for input config using parsers from this module."""

import json
import logging
from typing import Any, Sequence
import re

from prp.exceptions import UnsupportedMethod
from prp.models.enums import AnalysisType, AnalysisSoftware
from prp.models.base import ParserOutput
from prp.models.config import SampleConfig

from prp.models.phenotype import AMRMethodIndex, ElementType, PredictionSoftware, StressMethodIndex, VirulenceMethodIndex
from prp.models.sample import SCHEMA_VERSION, MethodIndex, PipelineResult, QcMethodIndex
from prp.models.species import SppMethodIndex, SppPredictionSoftware
from prp.models.typing import SccmecTypingMethodIndex, ShigaTypingMethodIndex, SpatyperTypingMethodIndex, TypingSoftware
from prp.models.typing import EmmTypingMethodIndex
from prp.parse.base import BaseParser, ParserInput
from .registry import register_parser, run_parser
from . import (
    hamronization,
    kleborate,
    resfinder,
    tbprofiler,
)
from .igv import parse_igv_info
from .metadata import parse_run_info
from .qc import (
    parse_gambitcore_results,
    parse_nanoplot_results,
    parse_postalignqc_results,
    parse_quast_results,
    parse_samtools_coverage_results,
)
from .typing import parse_cgmlst_results, parse_mlst_results

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



def _read_qc(smp_cnf) -> Sequence[QcMethodIndex]:
    """Read all qc related info"""
    qc_results = []
    if smp_cnf.quast:
        qc_results.append(parse_quast_results(smp_cnf.quast))

    if smp_cnf.postalnqc:
        qc_results.append(parse_postalignqc_results(smp_cnf.postalnqc))

    if smp_cnf.gambitcore:
        qc_results.append(parse_gambitcore_results(smp_cnf.gambitcore))

    if smp_cnf.nanoplot:
        qc_results.append(parse_nanoplot_results(smp_cnf.nanoplot))

    if smp_cnf.samtools:
        qc_results.append(parse_samtools_coverage_results(smp_cnf.samtools))

    return qc_results


def _read_spp_prediction(smp_cnf) -> Sequence[SppMethodIndex]:
    """Read all species prediction results."""
    spp_results = []
    if smp_cnf.kraken:
        out = run_parser(
            software=SppPredictionSoftware.BRACKEN.value, 
            version="1.0.0",
            data=smp_cnf.kraken
        )
        spp_results.append(SppMethodIndex(
            result=out.results,
        ))

    if smp_cnf.mykrobe:
        out = run_parser(
            software=PredictionSoftware.MYKROBE.value,
            version="1.0.0",
            data=smp_cnf.mykrobe
        )
        spp_results.append(
            SppMethodIndex(
                software=PredictionSoftware.MYKROBE,
                result=out.results["species"]
        ))
    return spp_results


def _read_typing(
    smp_cnf,
) -> Sequence[
    MethodIndex
    | EmmTypingMethodIndex
    | ShigaTypingMethodIndex
    | SccmecTypingMethodIndex
    | SpatyperTypingMethodIndex
]:
    """Read typing all information."""
    typing_result = []
    if smp_cnf.mlst:
        typing_result.append(parse_mlst_results(smp_cnf.mlst))

    if smp_cnf.chewbbaca:
        typing_result.append(parse_cgmlst_results(smp_cnf.chewbbaca))

    if smp_cnf.emmtyper:
        out = run_parser(
            software=AnalysisSoftware.EMMTYPER, 
            version="1.0.0",
            data=smp_cnf.emmtyper
        )
        typing_result.extend(EmmTypingMethodIndex(
            result=out.results
        ))

    if smp_cnf.shigapass:
        out = run_parser(
            software=AnalysisSoftware.SHIGAPASS,
            version="1.0.0",
            data=smp_cnf.shigapass
        )
        typing_result.append(
            ShigaTypingMethodIndex(
                result=out.results
            ))

    if smp_cnf.spatyper:
        out = run_parser(
            software=AnalysisSoftware.SPATYPER,
            version="1.0.0",
            data=smp_cnf.spatyper
        )
        typing_result.append(
            SpatyperTypingMethodIndex(
                result=out.results
            ))

    if smp_cnf.sccmec:
        out = run_parser(
            software=TypingSoftware.SCCMEC,
            version="1.0.0",
            data=smp_cnf.sccmec
        )
        first = out.results['sccmec'][0]
        typing_result.append(SccmecTypingMethodIndex(result=first))

    # stx typing
    if smp_cnf.virulencefinder:
        out = run_parser(
            software=AnalysisSoftware.VIRULENCEFINDER,
            version="1.0.0",
            data=smp_cnf.virulencefinder,
            want=AnalysisType.STX
        )
        typing_result.append(MethodIndex(
            software=TypingSoftware.VIRULENCEFINDER,
            type=AnalysisType.STX,
            result=out.results[AnalysisType.STX]
        ))

    if smp_cnf.serotypefinder:
        out = run_parser(
            software=AnalysisSoftware.SEROTYPEFINDER,
            version="1.0.0",
            data=smp_cnf.serotypefinder,
        )
        for atype in [AnalysisType.O_TYPE, AnalysisType.H_TYPE]:
            typing_result.extend(MethodIndex(
                software=AnalysisSoftware.SEROTYPEFINDER,
                type=atype,
                result=out.results[atype]
            ))

    if smp_cnf.mykrobe:
        out = run_parser(
            software=PredictionSoftware.MYKROBE.value,
            version="1.0.0",
            data=smp_cnf.mykrobe
        )
        typing_result.append(
            MethodIndex(
                software=PredictionSoftware.MYKROBE.value,
                result=out.results["lineage"]
            )
        )

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
                tmp_res = resfinder.parse_amr_pred(pred_res, method)
                if tmp_res.result.genes:
                    resistance.append(tmp_res)

    if smp_cnf.amrfinder:
        out = run_parser(software="amrfinder", version="1.0.0", data=smp_cnf.amrfinder)

        target = AnalysisType.AMR
        if target.value in out.result:
            # cast as method index and append to resistance results
            resistance.append(
                AMRMethodIndex(
                    software=PredictionSoftware.AMRFINDER,
                    result=out.result
                )
            )

        target = AnalysisType.STRESS
        if target.value in out.result:
            # cast as method index and append to resistance results
            resistance.append(
                StressMethodIndex(
                    software=PredictionSoftware.AMRFINDER,
                    result=out.result
                )
            )

    if smp_cnf.mykrobe:
        out = run_parser(
            software=PredictionSoftware.MYKROBE.value,
            version="1.0.0",
            data=smp_cnf.mykrobe
        )
        resistance.append(
            AMRMethodIndex(
                software=PredictionSoftware.MYKROBE.value,
                result=out.results["amr"]
            )
        )

    if smp_cnf.tbprofiler:
        # store pipeline version
        resistance.append(tbprofiler.parse_amr_pred(smp_cnf.tbprofiler))
    return resistance


def _read_virulence(smp_cnf) -> Sequence[VirulenceMethodIndex]:
    """Read virulence results."""
    virulence = []
    if smp_cnf.amrfinder:
        target = AnalysisType.VIRULENCE
        out = run_parser(software="amrfinder", version="1.0.0", data=smp_cnf.amrfinder, want=[target])
        if target.value in out.result:
            # cast as method index and append to resistance results
            virulence.append(
                VirulenceMethodIndex(
                    software=PredictionSoftware.AMRFINDER,
                    result=out.result
                )
            )

    if smp_cnf.virulencefinder:
        # virulence genes
        out = run_parser(
            software=AnalysisSoftware.VIRULENCEFINDER,
            version="1.0.0",
            data=smp_cnf.virulencefinder,
            want=AnalysisType.VIRULENCE
        )
        virulence.append(VirulenceMethodIndex(
            software=TypingSoftware.VIRULENCEFINDER,
            result=out.results[AnalysisType.VIRULENCE]
        ))
    return virulence


def parse_sample(smp_cnf: SampleConfig) -> PipelineResult:
    """Parse sample config object into a combined result object."""
    sample_info, seq_info, pipeline_info = parse_run_info(
        smp_cnf.nextflow_run_info, smp_cnf.software_info
    )
    results: dict[str, Any] = {
        "sequencing": seq_info,
        "pipeline": pipeline_info,
        "qc": _read_qc(smp_cnf),
        "species_prediction": _read_spp_prediction(smp_cnf),
        "typing_result": _read_typing(smp_cnf),
        "element_type_result": [],
        **sample_info,  # add sample_name & lims_id
    }
    if smp_cnf.ref_genome_sequence:
        (
            ref_genome_info,
            read_mapping,
            genome_annotation,
            filtered_variants,
        ) = parse_igv_info(
            smp_cnf.ref_genome_sequence,
            smp_cnf.ref_genome_annotation,
            smp_cnf.igv_annotations,
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
        [*_read_resistance(smp_cnf), *_read_virulence(smp_cnf)]
    )

    # add kleborate results
    # this is a test of a updated way of sorting outputs into their dedicated category
    if smp_cnf.kleborate and smp_cnf.kleborate_hamronization:
        with smp_cnf.kleborate_hamronization.open() as inpt:
            if (
                kleborate_version := hamronization.get_version(inpt)
            ) and kleborate_version is None:
                raise ValueError(
                    "Could not parse Kleborate version from hAMRonization file."
                )
        # reopen the file to get all entries
        with smp_cnf.kleborate_hamronization.open() as inpt:
            hamronization_entries = hamronization.parse_hamronization(inpt)
            analysis_results = kleborate.parse_kleborate_v3(
                path=smp_cnf.kleborate,
                version=kleborate_version.version,
                hamronization_entries=hamronization_entries,
            )

        # append the kleborate result to the individual categories in the result dict
        for res in analysis_results:
            # add new category if not previously defined
            if not res.target_field in results:
                results[res.target_field] = []
            results[res.target_field].append(res.data)

    # verify data consistancy
    return PipelineResult(
        sample_id=smp_cnf.sample_id, schema_version=SCHEMA_VERSION, **results
    )


@register_parser(MYKROBE)
class MykrobeParser(BaseParser):
    """Parser for Mykrobe results."""

    software = MYKROBE
    parser_name = "MykrobeParser"
    parser_version = "1"
    schema_version = 1
    produces = {AnalysisType.SPECIES, AnalysisType.AMR, AnalysisType.LINEAGE}

    def parse(self, data: ParserInput, *, want: set[AnalysisType], strict: bool) -> ParserOutput:
        """Parse output file."""

        want = want or self.produces

        out = ParserOutput(
            software=self.software,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            results={},
        )