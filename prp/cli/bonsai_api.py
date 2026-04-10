"""Functions for uploading results to Bonsai."""

import logging
import os

import click
from bonsai_libs.api_client.core.exceptions import ApiRequestFailed
from pydantic import ValidationError

from prp import VERSION as __version__
from prp.io.manifest import read_bootstrap_config
from prp.bonsai import BonsaiUploadService, make_bonsai_client
from prp.bonsai.service import UploadStateStore
from prp.exceptions import PrpError
from prp.models.manifest import SampleManifest
from prp.pipeline.loader import parse_manifest_for_upload

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
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force upload even if results already exist in Bonsai",
)
@click.argument(
    "manifest",
    type=SampleManifestFile(),
)
def bonsai_upload(
    manifest: SampleManifest,
    username: str,
    password: str,
    api_url: str,
    dry_run: bool,
    force: bool,
):
    """Upload a sample to Bonsai using either a sample config or json dump."""
    # setup state
    store = UploadStateStore(root=os.getcwd())

    # Parse sample config
    try:
        manifest_obj = parse_manifest_for_upload(manifest)
    except ValidationError as err:
        click.secho("Generated result failed validation", fg="red")
        click.secho(err)
        raise click.Abort("Upload aborted")

    # setup client connection and autenticate user
    client = make_bonsai_client(base_url=api_url)
    try:
        authenticated = client.authenticate_user(username=username, password=password)
    except ApiRequestFailed as exc:
        click.secho("Failed to authenticate to Bonsai API", fg="red")
        raise click.Abort() from exc
    if not authenticated:
        raise click.UsageError(
            "Could not authenticate to Bonsai API, check your credentials"
        )

    rid = manifest_obj.pipeline.pipeline_run_id
    workflow_id = f"bonsai-prp-upload-{manifest_obj.sample_id}-{rid}"
    service = BonsaiUploadService(
        client=client, state_store=store, workflow_id=workflow_id, dry_run=dry_run
    )
    try:
        service.upload_sample(manifest_obj, force=force)
    except PrpError as exc:
        LOG.info("Something went wrong uploading the sample, %s", exc)
        raise click.Abort("Uploaded aborted.") from exc

    # create a new sample
    click.secho("Sample uploaded", fg="green")


@bonsai_gr.command("bootstrap")
@click.option("-d", "--dry-run", is_flag=True)
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
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    default="bootstrap/default.yaml",
)
def bonsai_bootstrap(api_url: str, username: str, password: str, dry_run: bool, config_file: str) -> None:
    """Bootstrap a new test instance of Bonsai.
    
    CONFIG_FILE should be a YAML file containing users, groups, and samples to bootstrap.
    """
    # setup state
    store = UploadStateStore(root=os.getcwd())

    # Load configuration
    try:
        config = read_bootstrap_config(config_file)
    except Exception as exc:
        click.secho(f"Failed to load config file {config_file}: {exc}", fg="red")
        raise click.Abort()
    
    # Setup client (assuming admin credentials from env or config)
    client = make_bonsai_client(base_url=api_url)
    try:
        authenticated = client.authenticate_user(username=username, password=password)
    except ApiRequestFailed as exc:
        click.secho("Failed to authenticate to Bonsai API", fg="red")
        raise click.Abort() from exc
    if not authenticated:
        raise click.UsageError(
            "Could not authenticate to Bonsai API, check your credentials"
        )

    bootstrap_service = BonsaiUploadService(
        client=client, state_store=store, dry_run=dry_run
    )

    # Bootstrap users and groups
    LOG.info("Bootstraping users")
    for user in config.users:
        bootstrap_service.ensure_user_exists(user)

    LOG.info("Bootstraping groups")
    for group in config.groups:
        bootstrap_service.ensure_group_exists(group)
    
    click.secho("Bootstrap complete!", fg="green")