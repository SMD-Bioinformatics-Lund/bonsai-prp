"""Functions for parsing JASEN results and generating output Bonsai and CDM output files."""

import click
import logging
from pydantic import TypeAdapter, ValidationError
from pathlib import Path

from .utils import SampleConfigFile, OptionalFile
from prp.models.qc import QcMethodIndex, QcSoftware
from prp.models.sample import MethodIndex
from prp.models.config import SampleConfig
from prp.parse import (
    parse_cgmlst_results,
    parse_postalignqc_results,
    parse_quast_results,
    parse_sample,
    parse_alignment_results
)


LOG = logging.getLogger(__name__)


@click.group("parse")
def parse_gr():
    ...


@parse_gr.command()
@click.option(
    "-s",
    "--sample",
    "sample_cnf",
    type=SampleConfigFile(),
    help="Sample configuration with results.",
)
@click.option("-o", "--output", type=click.Path(), help="Path to result.")
def format_jasen(sample_cnf: SampleConfig, output: Path | None):
    """Parse JASEN results and write as concatenated file in json format."""
    LOG.info("Start generating pipeline result json")
    try:
        sample_obj = parse_sample(sample_cnf)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)
        raise click.Abort

    # Either write to stdout or to file
    dump = sample_obj.model_dump_json(indent=2)
    if output is None:
        print(dump)
    else:
        LOG.info("Storing results to: %s", output)
        try:
            with open(output, "w", encoding="utf-8") as fout:
                fout.write(dump)
        except Exception as _:
            raise click.Abort("Error writing results file")
    click.secho("Finished generating pipeline output", fg="green")


@parse_gr.command()
@click.option(
    "-s",
    "--sample",
    "sample_cnf",
    type=SampleConfigFile(),
    help="Sample configuration with results.",
)
@click.option(
    "-o", "--output", required=True, type=click.File("w"), help="output filepath"
)
def format_cdm(sample_cnf: SampleConfigFile, output: OptionalFile) -> None:
    """Format QC metrics into CDM compatible input file."""
    results: list[QcMethodIndex] = []
    if sample_cnf.postalnqc:
        LOG.info("Parse quality results")
        results.append(parse_postalignqc_results(sample_cnf.postalnqc))

    if sample_cnf.quast:
        LOG.info("Parse quast results")
        results.append(parse_quast_results(sample_cnf.quast))

    if sample_cnf.chewbbaca:
        LOG.info("Parse cgmlst results")
        res: MethodIndex = parse_cgmlst_results(sample_cnf.chewbbaca)
        n_missing_loci = QcMethodIndex(
            software=QcSoftware.CHEWBBACA, result={"n_missing": res.result.n_missing}
        )
        results.append(n_missing_loci)
    # cast output as pydantic type for easy serialization
    qc_data = TypeAdapter(list[QcMethodIndex])

    LOG.info("Storing results to: %s", output.name)
    output.write(qc_data.dump_json(results, indent=3).decode("utf-8"))
    click.secho("Finished generating QC output", fg="green")


@parse_gr.command()
@click.option("-i", "--sample-id", required=True, help="Sample identifier")
@click.option("-b", "--bam", required=True, type=click.File(), help="bam file")
@click.option("-e", "--bed", type=click.File(), help="bed file")
@click.option("-a", "--baits", type=click.File(), help="baits file")
@click.option(
    "-r", "--reference", required=True, type=click.File(), help="reference fasta"
)
@click.option("-c", "--cpus", type=click.INT, default=1, help="cpus")
@click.option(
    "-o", "--output", required=True, type=click.File("w"), help="output filepath"
)
def create_qc_result(sample_id: str, bam: click.File, bed: OptionalFile, baits: OptionalFile, reference: OptionalFile, cpus: int, output: click.File) -> None:
    """Generate QC metrics regarding bam file"""
    if bam and reference:
        LOG.info("Parse alignment results")
        parse_alignment_results(sample_id, bam, reference, cpus, output, bed, baits)
    click.secho("Finished generating QC output", fg="green")
