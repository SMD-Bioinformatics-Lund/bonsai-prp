"""Upload sample to Bonasi module."""

from pathlib import Path
from typing import Any

import click
import requests
from requests.exceptions import HTTPError
from requests.structures import CaseInsensitiveDict

from prp.models.metadata import MetaEntry
from prp.parse.metadata import process_custom_metadata

from ..models.config import SampleConfig
from ..models.sample import PipelineResult

from .auth import ConnectionInfo, api_authentication, TIMEOUT


@api_authentication
def upload_sample_result(
    headers: CaseInsensitiveDict[Any], api_url: str, sample_obj: PipelineResult
) -> str:
    """Create a new sample."""
    resp = requests.post(
        f"{api_url}/samples/",
        headers=headers,
        json=sample_obj.model_dump(mode="json"),
        timeout=TIMEOUT,
    )

    resp.raise_for_status()
    resp_data = resp.json()
    return resp_data["sample_id"]


@api_authentication
def upload_signature(
    headers: CaseInsensitiveDict[Any],
    api_url: str,
    sample_cnf: SampleConfig,
) -> str | None:
    """Upload a genome signature to sample."""
    if sample_cnf.sourmash_signature is not None:
        resp = requests.post(
            f"{api_url}/samples/{sample_cnf.sample_id}/signature",
            headers=headers,
            files={"signature": Path(sample_cnf.sourmash_signature).open()},
            timeout=TIMEOUT,
        )

        resp.raise_for_status()
        return resp.json()
    raise ValueError("No sourmash signature associated with sample")


@api_authentication
def add_ska_index(
    headers: CaseInsensitiveDict[Any],
    api_url: str,
    sample_cnf: SampleConfig,
) -> str:
    """Upload a genome signature to sample."""
    params: dict[str, str] = {"index": str(sample_cnf.ska_index)}
    resp = requests.post(
        f"{api_url}/samples/{sample_cnf.sample_id}/ska_index",
        headers=headers,
        params=params,
        timeout=TIMEOUT,
    )

    resp.raise_for_status()
    return resp.json()


@api_authentication
def add_sample_to_group(
    headers: CaseInsensitiveDict[Any], api_url: str, group_id: str, sample_id: str
) -> str:
    """Add sample to a group."""
    resp = requests.put(
        f"{api_url}/groups/{group_id}/samples",
        headers=headers,
        params={"s": sample_id},
        timeout=TIMEOUT,
    )

    resp.raise_for_status()
    return resp.json()


@api_authentication
def add_metadata_to_sample(
    headers: CaseInsensitiveDict[str],
    api_url: str,
    sample_id: str,
    metadata: list[MetaEntry],
):
    # process metadata
    serialized_data = [rec.model_dump() for rec in metadata]
    resp = requests.post(
        f"{api_url}/samples/{sample_id}/metadata",
        headers=headers,
        json=serialized_data,
        timeout=TIMEOUT,
    )

    resp.raise_for_status()
    return resp.json()


def _process_generic_status_codes(error: HTTPError, sample_id: str) -> tuple[str, bool]:
    """Process generic http status codes."""
    is_major_error = True
    match error.response.status_code:
        case 404:
            msg = f"Sample with {sample_id} is not in Bonsai"
            is_major_error = False
        case 500:
            msg = "An unexpected error occured in Bonsai, check bonsai api logs"
        case _:
            msg = f"An unknown error occurred; {str(error)}"
    return msg, is_major_error


def upload_sample(
    conn: ConnectionInfo, results: PipelineResult, cnf: SampleConfig
) -> str:
    """Upload a sample with files for clustring."""
    try:
        upload_sample_result(  # pylint: disable=no-value-for-parameter
            token_obj=conn.token, api_url=conn.api_url, sample_obj=results
        )
    except HTTPError as error:
        if error.response.status_code == 409:
            click.secho("Sample has already been uploaded", fg="yellow")
        else:
            msg, _ = _process_generic_status_codes(error, "")
            raise click.UsageError(msg) from error
    # upload minhash signature to sample
    if cnf.sourmash_signature is not None:
        try:
            upload_signature(  # pylint: disable=no-value-for-parameter
                token_obj=conn.token, api_url=conn.api_url, sample_cnf=cnf
            )
        except HTTPError as error:
            if error.response.status_code == 409:
                click.secho(
                    f"Sample {cnf.sample_id} has already a signature file, skipping",
                    fg="yellow",
                )
            else:
                msg, _ = _process_generic_status_codes(error, cnf.sample_id)
                raise click.UsageError(msg) from error
    # add ska index path to sample
    if cnf.ska_index is not None:
        try:
            add_ska_index(  # pylint: disable=no-value-for-parameter
                token_obj=conn.token, api_url=conn.api_url, sample_cnf=cnf
            )
        except HTTPError as error:
            if error.response.status_code == 409:
                click.secho(
                    (
                        f"Sample {cnf.sample_id} is already associated "
                        "with a ska index file, skipping"
                    ),
                    fg="yellow",
                )
            else:
                msg, _ = _process_generic_status_codes(error, cnf.sample_id)
                raise click.UsageError(msg) from error
    # add metadata to an existing sample
    if len(cnf.metadata) > 0:
        records = process_custom_metadata(cnf.metadata)
        try:
            add_metadata_to_sample(
                token_obj=conn.token,
                api_url=conn.api_url,
                sample_id=cnf.sample_id,
                metadata=records,
            )
        except HTTPError as error:
            if error.response.status_code == 422:
                fmt_records = [rec.model_dump_json() for rec in records]
                click.secho(f"Bad formatting of input data, {fmt_records}", fg="yellow")
            else:
                msg, _ = _process_generic_status_codes(error, cnf.sample_id)
                raise click.UsageError(msg) from error
    return cnf.sample_id
