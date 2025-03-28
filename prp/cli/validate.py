"""Commands for validating and migrating data."""
import json
import logging
from typing import TextIO

import click
from pydantic import ValidationError

from prp import VERSION as __version__

from prp.models.sample import PipelineResult

LOG = logging.getLogger(__name__)


@click.group("validate")
def validate_gr():
    ...


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
        PipelineResult.model_validate_json(js)
    except ValidationError as err:
        click.secho("Invalid file format X", fg="red")
        click.secho(err)
    else:
        click.secho(f'The file "{output.name}" is valid', fg="green")