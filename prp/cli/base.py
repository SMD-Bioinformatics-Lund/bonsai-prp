"""Definition of the PRP command-line interface."""

import logging

import click

from prp import VERSION as __version__

from .bonsai_api import bonsai_gr

LOG = logging.getLogger(__name__)


@click.group()
@click.version_option(__version__)
@click.option("-s", "--silent", is_flag=True)
@click.option("-d", "--debug", is_flag=True)
def cli(silent: bool, debug: bool):
    """Jasen pipeline result processing tool."""
    if silent:
        log_level = logging.ERROR
    elif debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARNING
    # configure logging
    logging.basicConfig(
        level=log_level, format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )


# add commands
cli.add_command(bonsai_gr)
