"""Definition of the PRP command-line interface."""

import json
import logging
from pathlib import Path

import click
import numpy as np
import pandas as pd
import pysam
from cyvcf2 import VCF, Writer
from pydantic import TypeAdapter, ValidationError
import yaml

from prp import VERSION as __version__

from .models.qc import QcMethodIndex, QcSoftware
from .models.sample import MethodIndex, PipelineResult, IgvAnnotationTrack
from .models.config import SampleConfig
from .parse import (
    parse_alignment_results,
    parse_cgmlst_results,
    parse_postalignqc_results,
    parse_quast_results,
    parse_sample
)
from .parse.utils import parse_input_dir
from .parse.variant import annotate_delly_variants
from . import bonsai

LOG = logging.getLogger(__name__)

OUTPUT_SCHEMA_VERSION = 1
USER_ENV = "BONSAI_USER"
PASSWD_ENV = "BONSAI_PASSWD"

class SampleConfigFile(click.ParamType):
    name = "config"

    def convert(self, value, param, ctx):
        """Convert string path to yaml object."""
        # verify input is path to existing file
        try:
            cnf_path = Path(value)
            if not cnf_path.is_file():
                raise FileNotFoundError(f"file {cnf_path.name} not found, please check the path.")
        except TypeError as error:
            raise TypeError(f"value should be a str not '{type(value)}'") from error
        # load yaml and cast to pydantic model
        with cnf_path.open() as cfile:
            data = yaml.safe_load(cfile)
            return SampleConfig(**data)


class JsonFile(click.ParamType):
    name = "config"

    def convert(self, value, param, ctx):
        """Convert string path to yaml object."""
        # verify input is path to existing file
        try:
            file_path = Path(value)
            if not file_path.is_file():
                raise FileNotFoundError(f"file not found, please check the path.")
        except TypeError as error:
            raise TypeError(f"value should be a str not '{type(value)}'") from error
        # load yaml and cast to pydantic model
        with file_path.open() as cfile:
            return json.load(cfile)


@click.group()
@click.version_option(__version__)
@click.option("-s", "--silent", is_flag=True)
@click.option("-d", "--debug", is_flag=True)
def cli(silent, debug):
    """Jasen pipeline result processing tool."""
    if silent:
        log_level = logging.WARNING
    elif debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    # configure logging
    logging.basicConfig(
        level=log_level, format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )


@cli.command()
@click.option("-s", "--sample", 'sample_cnf', type=SampleConfigFile(), help="Sample configuration with results.")
@click.option("-a", "--api", "api_url", required=True, type=str, help="Upload configuration")
@click.option("-u", "--username", required=True, envvar=USER_ENV, type=str, help="Username")
@click.option("-p", "--password", required=True, envvar=PASSWD_ENV, type=str, help="Password")
def upload(sample_cnf, username, password, api_url):
    """Upload a sample to Bonsai using either a sample config or json dump."""
    # Parse sample config
    try:
        sample_obj = parse_sample(sample_cnf)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)

    # Authenticate to Bonsai API
    try:
        conn = bonsai.authenticate(api_url, username, password)
    except ValueError as error:
        raise click.UsageError(str(error)) from error

    # Upload sample
    bonsai.upload_sample(conn, sample_obj, sample_cnf)
    # add sample to group if it was assigned one.
    for group_id in sample_cnf.groups:
        try:
            bonsai.add_sample_to_group(  # pylint: disable=no-value-for-parameter
                token_obj=conn.token, api_url=conn.api_url, group_id=group_id, sample_id=sample_cnf.sample_id
            )
        except bonsai.HTTPError as error:
            match error.response.status_code:
                case 404:
                    msg = f"Group with id {group_id} is not in Bonsai"
                case 500:
                    msg = "An unexpected error occured in Bonsai, check bonsai api logs"
                case _:
                    msg = f"An unknown error occurred; {str(error)}"
            # raise error and abort execution
            raise click.UsageError(msg) from error
    # exit script
    click.secho("Sample uploaded", fg="green")


@cli.command()
@click.option("-s", "--sample", 'sample_cnf', type=SampleConfigFile(), required=True, help="Sample configuration with results.")
@click.option("-o", "--output", type=click.Path(), help="Path to result.")
def parse(sample_cnf, output):
    """Parse JASEN resulst and write as concatinated file in json format."""
    LOG.info("Start generating pipeline result json")
    try:
        sample_obj = parse_sample(sample_cnf)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)
        raise click.Abort

    # Either wrtie to stdout or to file
    dump = sample_obj.model_dump_json(indent=2)
    if output is None:
        print(dump)
    else:
        LOG.info("Storing results to: %s", output)
        try:
            with open(output, "w", encoding="utf-8") as fout:
                fout.write(dump)
        except Exception as error:
            raise click.Abort('Error writing results file')
    click.secho("Finished generating pipeline output", fg="green")


@cli.command()
@click.option(
    "-i",
    "--input-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Input directory to JASEN's outdir incl. speciesDir",
)
@click.option(
    "-j",
    "--jasen-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to JASEN directory",
)
@click.option(
    "-s",
    "--symlink-dir",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to symlink directory",
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory to incl. speciesDir [default: input_dir]",
)
@click.pass_context
def rerun_bonsai_input(ctx, input_dir, jasen_dir, symlink_dir, output_dir) -> None:
    """Rerun bonsai input creation for all samples in input directory."""
    if input_dir:
        LOG.info("Parse input directory")
        input_arrays = parse_input_dir(input_dir, jasen_dir, symlink_dir, output_dir)
        for input_array in input_arrays:
            pass
            #ctx.invoke(create_bonsai_input, **input_array)


@cli.command()
def print_schema():
    """Print Pipeline result output format schema."""
    click.secho(PipelineResult.schema_json(indent=2))


@cli.command()
@click.option("-o", "--output", required=True, type=click.File("r"))
def validate(output):
    """Validate output format of result json file."""
    js = json.load(output)
    try:
        PipelineResult(**js)
    except ValidationError as err:
        click.secho("Invalid file format X", fg="red")
        click.secho(err)
    else:
        click.secho(f'The file "{output.name}" is valid', fg="green")


@cli.command()
@click.option("-q", "--quast", type=click.Path(), help="Quast quality control metrics")
@click.option("-p", "--quality", type=click.Path(), help="postalignqc qc results")
@click.option("-c", "--cgmlst", type=click.Path(), help="cgMLST prediction results")
@click.option("--correct_alleles", is_flag=True, help="Correct alleles")
@click.option(
    "-o", "--output", required=True, type=click.File("w"), help="output filepath"
)
def create_cdm_input(quast, quality, cgmlst, correct_alleles, output) -> None:
    """Format QC metrics into CDM compatible input file."""
    results = []
    if quality:
        LOG.info("Parse quality results")
        res: QcMethodIndex = parse_postalignqc_results(quality)
        results.append(res)

    if quast:
        LOG.info("Parse quast results")
        res: QcMethodIndex = parse_quast_results(quast)
        results.append(res)

    if cgmlst:
        LOG.info("Parse cgmlst results")
        res: MethodIndex = parse_cgmlst_results(cgmlst, correct_alleles=correct_alleles)
        n_missing_loci = QcMethodIndex(
            software=QcSoftware.CHEWBBACA, result={"n_missing": res.result.n_missing}
        )
        results.append(n_missing_loci)
    # cast output as pydantic type for easy serialization
    qc_data = TypeAdapter(list[QcMethodIndex])

    LOG.info("Storing results to: %s", output.name)
    output.write(qc_data.dump_json(results, indent=3).decode("utf-8"))
    click.secho("Finished generating QC output", fg="green")


@cli.command()
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
def create_qc_result(sample_id, bam, bed, baits, reference, cpus, output) -> None:
    """Generate QC metrics regarding bam file"""
    if bam and reference:
        LOG.info("Parse alignment results")
        parse_alignment_results(sample_id, bam, reference, cpus, output, bed, baits)
    click.secho("Finished generating QC output", fg="green")


@cli.command()
@click.option("-v", "--vcf", type=click.Path(exists=True), help="VCF file")
@click.option("-b", "--bed", type=click.Path(exists=True), help="BED file")
@click.option(
    "-o",
    "--output",
    required=True,
    type=click.Path(writable=True),
    help="output filepath",
)
def annotate_delly(vcf, bed, output):
    """Annotate Delly SV varinats with genes in BED file."""
    output = Path(output)
    # load annotation
    if bed is not None:
        annotation = pysam.TabixFile(bed, parser=pysam.asTuple())
    else:
        raise click.UsageError("You must provide a annotation file.")

    vcf_obj = VCF(vcf)
    variant = next(vcf_obj)
    annot_chrom = False
    if not variant.CHROM in annotation.contigs:
        if len(annotation.contigs) > 1:
            raise click.UsageError(
                (
                    f'"{variant.CHROM}" not in BED file'
                    " and the file contains "
                    f"{len(annotation.contigs)} chromosomes"
                )
            )
        # if there is only one "chromosome" in the bed file
        annot_chrom = True
        LOG.warning("Annotating variant chromosome to %s", annotation.contigs[0])
    # reset vcf file
    vcf_obj = VCF(vcf)
    vcf_obj.add_info_to_header(
        {
            "ID": "gene",
            "Description": "overlapping gene",
            "Type": "Character",
            "Number": "1",
        }
    )
    vcf_obj.add_info_to_header(
        {
            "ID": "locus_tag",
            "Description": "overlapping tbdb locus tag",
            "Type": "Character",
            "Number": "1",
        }
    )

    # open vcf writer
    writer = Writer(output.absolute(), vcf_obj)
    annotate_delly_variants(writer, vcf_obj, annotation, annot_chrom=annot_chrom)

    click.secho(f"Wrote annotated delly variants to {output.name}", fg="green")


@cli.command()
@click.option("-n", "--track-name", type=str, help="Track name.")
@click.option(
    "-a", "--annotation-file", type=click.Path(exists=True), help="Path to file."
)
@click.option(
    "-b",
    "--bonsai-input-file",
    required=True,
    type=click.Path(writable=True),
    help="PRP result file (used as bonsai input).",
)
@click.option(
    "-o",
    "--output",
    required=True,
    type=click.File("w"),
    help="output filepath",
)
def add_igv_annotation_track(track_name, annotation_file, bonsai_input_file, output):
    """Add IGV annotation track to result (bonsai input file)."""
    with open(bonsai_input_file, "r", encoding="utf-8") as jfile:
        result_obj = PipelineResult(**json.load(jfile))

    # Get genome annotation
    if not isinstance(
        result_obj.genome_annotation, list
    ):
        track_info = []
    else:
        track_info = result_obj.genome_annotation

    # add new tracks
    track_info.append(IgvAnnotationTrack(name=track_name, file=annotation_file))

    # update data model
    upd_result = result_obj.model_copy(update={"genome_annotation": track_info})

    # overwrite result
    output.write(upd_result.model_dump_json(indent=3))

    click.secho(f"Wrote updated result to {output.name}", fg="green")
