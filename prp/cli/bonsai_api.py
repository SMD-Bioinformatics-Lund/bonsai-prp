"""Functions for uploading results to Bonsai."""

import logging
import os

import click
from pydantic import ValidationError

from prp import VERSION as __version__
from prp.bonsai import BonsaiUploadService, make_bonsai_client
from prp.bonsai.service import UploadStateStore
from prp.models.manifest import SampleManifest
from prp.pipeline.loader import parse_results_from_manifest

from .utils import SampleManifestFile

LOG = logging.getLogger(__name__)

USER_ENV = "BONSAI_USER"
PASSWD_ENV = "BONSAI_PASSWD"


@click.group("bonsai")
def bonsai_gr():
    """Interact with the Bonsai API."""


@bonsai_gr.command("upload")
@click.option(
    "-a", "--api", "api_url", required=True, type=str, help="Upload configuration"
)
@click.option(
    "-u", "--username", required=True, envvar=USER_ENV, type=str, help="Username"
)
@click.option(
    "-p", "--password", required=True, envvar=PASSWD_ENV, type=str, help="Password"
)
@click.option("-d", "--dry-run", is_flag=True)
@click.argument(
    "manifest",
    type=SampleManifestFile(),
)
def bonsai_upload(
    manifest: SampleManifest, username: str, password: str, api_url: str, dry_run: bool
):
    """Upload a sample to Bonsai using either a sample config or json dump."""
    # setup state
    store = UploadStateStore(root=os.getcwd())

    # Parse sample config
    try:
        manifest_obj = parse_results_from_manifest(manifest)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)
        raise click.Abort("Upload aborted")

    # setup client connection and autenticate user
    client = make_bonsai_client(base_url=api_url)
    authenticated = client.authenticate_user(username=username, password=password)
    if not authenticated:
        raise click.UsageError(
            "Could not authenticate to Bonsai API, check your credentials"
        )

    service = BonsaiUploadService(client=client, state_store=store, dry_run=dry_run)
    try:
        service.upload_sample(manifest_obj)
    except Exception as exc:
        LOG.exception("Something went wrong uploading the sample, %s", exc)
        raise click.Abort("An error prevented the sample from being uploaded.")

    # create a new sample
    click.secho("Sample uploaded", fg="green")
