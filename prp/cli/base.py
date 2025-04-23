"""Definition of the PRP command-line interface."""

import logging

import click

from prp import VERSION as __version__

from . import annotate, parse, upload, validate

LOG = logging.getLogger(__name__)


@click.group()
@click.version_option(__version__)
@click.option("-s", "--silent", is_flag=True)
@click.option("-d", "--debug", is_flag=True)
def cli(silent: bool, debug: bool):
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


# add commands

## for manipulating jasen results
cli.add_command(parse.format_jasen)
cli.add_command(validate.validate_result)
cli.add_command(validate.migrate_result)
cli.add_command(annotate.annotate_delly)
cli.add_command(annotate.add_igv_annotation_track)
## qc related
cli.add_command(parse.format_cdm)
cli.add_command(parse.create_qc_result)
cli.add_command(validate.print_schema)
## bonsai reslated
cli.add_command(upload.bonsai_upload)
