"""Commands to annotate existing results with new data."""

import json
import logging
from pathlib import Path

import click
import pysam
from cyvcf2 import VCF, Writer

from prp import VERSION as __version__
from prp.models.sample import IgvAnnotationTrack, PipelineResult
from prp.parse.variant import annotate_delly_variants

LOG = logging.getLogger(__name__)


@click.group("annotate")
def annotate_gr(): ...


@annotate_gr.command()
@click.option("-v", "--vcf", type=click.Path(exists=True), help="VCF file")
@click.option("-b", "--bed", type=click.Path(exists=True), help="BED file")
@click.option(
    "-o",
    "--output",
    required=True,
    type=click.Path(writable=True),
    help="output filepath",
)
def annotate_delly(vcf: Path | None, bed: Path | None, output: Path):
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


@annotate_gr.command()
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
    if not isinstance(result_obj.genome_annotation, list):
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
