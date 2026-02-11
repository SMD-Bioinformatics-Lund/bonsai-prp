"""Functions for parsing JASEN results and generating output Bonsai and CDM output files."""

import logging
from pathlib import Path

import click
from prp.analysis.qc import parse_alignment_results
from prp.parse.models.enums import AnalysisSoftware, AnalysisType
from prp.parse.core.registry import run_parser
from prp.pipeline.sample import parse_results_from_manifest
from pydantic import TypeAdapter, ValidationError

from prp.models.manifest import SampleManifest
from prp.parse.models.enums import AnalysisSoftware
from prp.pipeline.types import CdmQcMethodIndex, QcMethodIndex
from prp.export import to_result_json

from .utils import OptionalFile, SampleManifestFile

LOG = logging.getLogger(__name__)


@click.group("parse")
def parse_gr():
    """Read and format pipeline results."""


@parse_gr.command("jasen")
@click.option("-o", "--output", type=click.Path(), help="Path to result.")
@click.argument(
    "manifest",
    type=SampleManifestFile(),
)
def format_results(manifest: SampleManifest, output: Path | None):
    """Parse JASEN results and serialize it in json format."""
    LOG.info("Start generating pipeline result json")
    try:
        results_obj = parse_results_from_manifest(manifest)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)
        raise click.Abort

    # Either write to stdout or to file
    blob = to_result_json(results_obj)
    if output is None:
        print(blob)
    else:
        LOG.info("Storing results to: %s", output)
        try:
            with open(output, "w", encoding="utf-8") as fout:
                fout.write(blob)
        except Exception as _:
            raise click.Abort("Error writing results file")
    click.secho("Finished generating pipeline output", fg="green")


@parse_gr.command("format-cdm")
@click.option(
    "-s",
    "--sample",
    "sample_cnf",
    type=SampleManifestFile(),
    help="Sample configuration with results.",
)
@click.option(
    "-o", "--output", required=True, type=click.File("w"), help="output filepath"
)
def format_cdm(sample_cnf: SampleManifestFile, output: OptionalFile) -> None:
    """Format QC metrics into CDM compatible input file."""
    results: list[QcMethodIndex] = []
    if sample_cnf.postalnqc:
        LOG.info("Parse quality results")
        
        out = run_parser(AnalysisSoftware.POSTALIGNQC, version="1.0.0", data=sample_cnf.postalnqc)
        res = out.results[AnalysisType.QC]
        if res.status != "parsed":
            LOG.warning(res.reason)
        else:
            results.append(
                CdmQcMethodIndex(id="postalignqc", software="postalignqc", result=res.value.model_dump())
            )

    if sample_cnf.quast:
        out = run_parser(AnalysisSoftware.QUAST, version="1.0.0", data=sample_cnf.quast)
        res = out.results[AnalysisType.QC]
        if res.status != "parsed":
            LOG.warning(res.reason)
        else:
            results.append(CdmQcMethodIndex(id="quast", software="quast", result=res.value.model_dump()))

    if sample_cnf.gambitcore:
        out = run_parser(AnalysisSoftware.GAMBIT, version="1.0.0", data=sample_cnf.gambitcore)
        res = out.results[AnalysisType.QC]
        if res.status != "parsed":
            LOG.warning(res.reason)
        else:
            results.append(CdmQcMethodIndex(id="gambitcore", software="gambitcore", result=res.value.model_dump()))

    if sample_cnf.chewbbaca:
        out = run_parser(AnalysisSoftware.CHEWBBACA, version="1.0.0", data=sample_cnf.chewbbaca)
        res = out.results[AnalysisType.CGMLST]
        if res.status != "parsed":
            LOG.warning(res.reason)
        else:
            missing_loci = res.value.n_missing
            n_missing_loci = QcMethodIndex(
                software=AnalysisSoftware.CHEWBBACA, result={"n_missing": missing_loci}
            )
            results.append(
                CdmQcMethodIndex(id="chewbbaca_missing_loci", **n_missing_loci.model_dump())
            )

    # cast output as pydantic type for easy serialization
    qc_data = TypeAdapter(list[CdmQcMethodIndex])

    LOG.info("Storing results to: %s", output.name)
    output.write(qc_data.dump_json(results, indent=3).decode("utf-8"))
    click.secho("Finished generating QC output", fg="green")
