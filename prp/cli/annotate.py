"""Commands to annotate existing results with new data."""

import json
import logging

import click

from prp.models.sample import IgvAnnotationTrack, PipelineResult

LOG = logging.getLogger(__name__)


@click.group("annotate")
def annotate_gr():
    """Annotate existing results with new data."""


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
