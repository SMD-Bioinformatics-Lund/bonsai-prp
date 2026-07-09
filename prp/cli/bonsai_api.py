"""Functions for uploading results to Bonsai."""

import logging
import os

import click
from pydantic import ValidationError

from bonsai_libs.api_client.core.exceptions import ApiRequestFailed, ServerError

from prp.bonsai import BonsaiUploadService, make_bonsai_client
from prp.bonsai.service import UploadStateStore
from prp.exceptions import PrpError
from prp.io.manifest import read_bootstrap_config
from prp.models.manifest import SampleManifest
from prp.pipeline.loader import parse_manifest_for_upload

from .utils import SampleManifestFile

LOG = logging.getLogger(__name__)

USER_ENV = "BONSAI_USER"
PASSWD_ENV = "BONSAI_PASSWD"
BONSAI_API_ENV = "BONSAI_API"


@click.group("bonsai")
def bonsai_gr():
    """Interact with the Bonsai API."""


@bonsai_gr.command("upload")
@click.option(
    "-a",
    "--api",
    "api_url",
    required=True,
    envvar=BONSAI_API_ENV,
    type=str,
    help="Upload configuration",
)
@click.option(
    "-u", "--username", required=True, envvar=USER_ENV, type=str, help="Username"
)
@click.option(
    "-p", "--password", required=True, envvar=PASSWD_ENV, type=str, help="Password"
)
@click.option("-d", "--dry-run", is_flag=True)
@click.option(
    "-i",
    "--ignore-errors",
    is_flag=True,
    help="Continue uploading even if some steps fail",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force upload even if results already exist in Bonsai",
)
@click.option(
    "--only",
    multiple=True,
    metavar="SOFTWARE",
    help=(
        "Upload only the result(s) from the given software (e.g. 'chewbbaca') "
        "onto an already-existing sample, skipping sample creation and other "
        "steps. Repeatable. The manifest's sample_id must be the existing "
        "Bonsai sample id. Combine with --force to overwrite the existing result."
    ),
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
    ignore_errors: bool,
    force: bool,
    only: tuple[str, ...],
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
    except (ApiRequestFailed, ServerError) as exc:
        click.secho("Failed to authenticate to Bonsai API", fg="red")
        raise click.Abort() from exc
    if not authenticated:
        raise click.UsageError(
            "Could not authenticate to Bonsai API, check your credentials"
        )

    only_set = {software.lower() for software in only}
    if only_set and not force:
        click.secho(
            "--only replaces existing results; combine with --force to overwrite them",
            fg="yellow",
        )

    rid = manifest_obj.pipeline.pipeline_run_id
    workflow_id = f"bonsai-prp-upload-{manifest_obj.sample_id}-{rid}"
    service = BonsaiUploadService(
        client=client, state_store=store, workflow_id=workflow_id,
        dry_run=dry_run, ignore_errors=ignore_errors
    )
    try:
        service.upload_sample(manifest_obj, force=force, only=only_set or None)
    except PrpError as exc:
        LOG.info("Something went wrong uploading the sample, %s", exc)
        raise click.Abort("Uploaded aborted.") from exc

    # create a new sample
    if only_set:
        click.secho(
            f"Uploaded result(s) for: {', '.join(sorted(only_set))}", fg="green"
        )
    else:
        click.secho("Sample uploaded", fg="green")


@bonsai_gr.command("bootstrap")
@click.option("-d", "--dry-run", is_flag=True)
@click.option(
    "-a",
    "--api",
    "api_url",
    required=True,
    envvar=BONSAI_API_ENV,
    type=str,
    help="Upload configuration",
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
def bonsai_bootstrap(
    api_url: str, username: str, password: str, dry_run: bool, config_file: str
) -> None:
    """Bootstrap a new test instance of Bonsai.

    CONFIG_FILE is a YAML file of users, groups, and samples to bootstrap.
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
        client=client, state_store=store, dry_run=dry_run, ignore_errors=True
    )

    # Bootstrap users and groups
    LOG.info("Bootstraping users")
    for user in config.users:
        bootstrap_service.ensure_user_exists(user)

    LOG.info("Bootstraping groups")
    for group in config.groups:
        bootstrap_service.ensure_group_exists(group)

    LOG.info("Bootstraping reference genomes")
    for ref in config.reference_genomes:
        bootstrap_service.ensure_reference_genome_exists(ref)

    click.secho("Bootstrap complete!", fg="green")
