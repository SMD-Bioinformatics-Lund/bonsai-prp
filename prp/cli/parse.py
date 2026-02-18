"""Functions for parsing JASEN results and generating output Bonsai and CDM output files."""

import json
import logging
from pathlib import Path

import click
from pydantic import ValidationError

from prp.export import to_cdm_format, to_result_json
from prp.models.manifest import SampleManifest
from prp.pipeline.loader import parse_results_from_manifest

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
@click.argument(
    "manifest",
    type=SampleManifestFile(),
)
@click.option("-o", "--output", type=click.File("w"), help="output filepath")
def format_cdm(manifest: SampleManifestFile, output: OptionalFile) -> None:
    """Format QC metrics into CDM compatible input file."""
    try:
        results_obj = parse_results_from_manifest(manifest)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)
        raise click.Abort

    cdm_result = to_cdm_format(results_obj)
    serialized = [e.model_dump(mode="json") for e in cdm_result]
    if output is None:
        print(json.dumps(serialized, indent=3))
    else:
        LOG.info("Storing results to: %s", output.name)
        try:
            print(json.dumps(serialized, indent=3), file=output)
        except Exception as _:
            raise click.Abort("Error writing results file")
    click.secho("Finished generating QC output", fg="green")
