"""Functions for uploading results to Bonsai."""

import logging

import click
from pydantic import ValidationError
from requests import HTTPError

from prp import VERSION as __version__
from prp import bonsai
from prp.models.config import SampleConfig
from prp.parse import parse_sample

from .utils import SampleConfigFile

LOG = logging.getLogger(__name__)

USER_ENV = "BONSAI_USER"
PASSWD_ENV = "BONSAI_PASSWD"


@click.group()
def upload(): ...


@upload.command()
@click.option(
    "-a", "--api", "api_url", required=True, type=str, help="Upload configuration"
)
@click.option(
    "-u", "--username", required=True, envvar=USER_ENV, type=str, help="Username"
)
@click.option(
    "-p", "--password", required=True, envvar=PASSWD_ENV, type=str, help="Password"
)
@click.argument(
    "sample_cnf",
    type=SampleConfigFile(),
)
def bonsai_upload(sample_cnf: SampleConfig, username: str, password: str, api_url: str):
    """Upload a sample to Bonsai using either a sample config or json dump."""
    # Parse sample config
    try:
        sample_obj = parse_sample(sample_cnf)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)
        click.Abort("Upload aborted")

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
                token_obj=conn.token,
                api_url=conn.api_url,
                group_id=group_id,
                sample_id=sample_cnf.sample_id,
            )
        except HTTPError as error:
            match error.response.status_code:
                case 404:
                    msg = f"Group with id {group_id} is not in Bonsai"
                case 500:
                    msg = (
                        "Please ensure that you have added the respective sample's group as a group in Bonsai. "
                        "Otherwise, an unexpected error occured in Bonsai, check bonsai api logs by running:\n"
                        "(sudo) docker logs api"
                    )
                case _:
                    msg = f"An unknown error occurred; {str(error)}"
            # raise error and abort execution
            raise click.UsageError(msg) from error
    # exit script
    click.secho("Sample uploaded", fg="green")
