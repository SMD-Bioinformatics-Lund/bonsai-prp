"""Commands for validating and migrating data."""

import json
import logging
from typing import TextIO

import click
from pydantic import ValidationError

from prp import VERSION as __version__
from prp.migration import migrate_result as migrate_result_json
from prp.models.sample import PipelineResult

LOG = logging.getLogger(__name__)


@click.group("validate")
def validate_gr(): ...


@validate_gr.command()
def print_schema():
    """Print Pipeline result output format schema."""
    click.secho(message=PipelineResult.model_json_schema(indent=2))


@validate_gr.command()
@click.option("-o", "--output", required=True, type=click.File("r"))
def validate_result(output: TextIO):
    """Validate a JASEN result file."""
    js = json.load(output)
    try:
        PipelineResult.model_validate(js)
    except ValidationError as err:
        click.secho("Invalid file format X", fg="red")
        click.secho(err)
    else:
        click.secho(f'The file "{output.name}" is valid', fg="green")


@validate_gr.command()
@click.argument("old_result", type=click.File("r"))
@click.argument("new_result", type=click.File("w"))
def migrate_result(old_result: TextIO, new_result: TextIO):
    """Migrate a old JASEN result blob to the current version."""

    js = json.load(old_result)
    migrated_result = migrate_result_json(js)

    # validate schema
    sample_obj = PipelineResult.model_validate(migrated_result)
    try:
        LOG.info("writing migrated result to: %s", new_result.name)
        new_result.write(sample_obj.model_dump_json(indent=2))
    except Exception as _:
        raise click.Abort("Error writing results file")
    click.secho("Finished migrating result", fg="green")
