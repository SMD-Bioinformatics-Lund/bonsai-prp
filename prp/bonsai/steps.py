"""Functions for steps in the Bonsai upload pipeline."""

import json
from functools import wraps
from typing import Any, Callable, TypeAlias
from pathlib import Path

from bonsai_libs.api_client.core.exceptions import ClientError
from bonsai_libs.api_client.bonsai.models import GenomicResourceInput, AnnotationTrack

from prp.exceptions import PrpError
from prp.pipeline.types import (
    IgvAnnotationTrack,
    MinimalAnalysisRecord,
    ParsedSampleResults,
)

from . import mappers
from .client import BonsaiApiClient
from .state_store import UploadState

Headers: TypeAlias = dict[str, str]
OpHeaders: TypeAlias = Headers | None

STEP_REGISTRY: dict[str, Callable[[], Any]] = {}
EXPECTED_SUFFIXES = ['vcf', 'bam', 'cram', 'gff', 'gff3', 'gtf', 'bed', 'bp']


def lookup_step(step_name: str) -> Callable[[], Any]:
    """Lookup a step function by name."""
    step_fn = STEP_REGISTRY.get(step_name)
    if not step_fn:
        raise ValueError(f"Step '{step_name}' is not registered.")
    return step_fn


def step(step_flag: str):
    """
    Decorator that wraps a step function so it automatically handles:
    - reporter callbacks
    - dry_run behaviour
    - updating UploadState
    - error reporting
    - consistent logging
    """

    def decorator(fn):

        @wraps(fn)
        def wrapper(
            service,
            client,
            sample_info,
            state: UploadState,
            *,
            headers: OpHeaders = None,
            dry_run: bool = False,
            ignore_errors: bool = False,
            substep: str | None = None,
            **kwargs,
        ):

            dynamic_id = f"{step_flag}:{substep}" if substep else step_flag
            external_id = state.sample_external_id

            service.reporter.on_step_start(external_id, dynamic_id)

            # Generate headers for consistent handling and logging.
            headers = headers or {}

            try:
                if dry_run:
                    # assign ID if needed, but do NOT call the API
                    if state.sample_id is None:
                        state.sample_id = "dry-run-sample-id"
                    state.mark(dynamic_id, {"dry_run": True})
                    service.state_store.save(state)
                    service.reporter.on_step_success(external_id, dynamic_id)
                    return None

                # normal execution
                result = fn(client, sample_info, state, headers=headers, **kwargs)
                state.mark(dynamic_id, {"response": result})
                service.state_store.save(state)
                service.reporter.on_step_success(external_id, dynamic_id)
                return result

            except ClientError as exc:
                # Try to extract meaningful error details from the API response,
                # but fall back to raw body if parsing fails
                try:
                    content = json.loads(exc.body) if exc.body else {}
                    details = content.get("detail", exc.body)
                except json.JSONDecodeError:
                    details = exc.body
                service.reporter.on_step_fail(external_id, dynamic_id, details)

                if not ignore_errors:
                    raise PrpError(
                        f"API error during step '{dynamic_id}': {details}"
                    ) from exc
            except Exception as exc:
                # Fallback error
                service.reporter.on_step_fail(external_id, dynamic_id, exc)
                raise

        STEP_REGISTRY[step_flag] = (
            wrapper  # register the step function for potential dynamic use
        )
        return wrapper

    return decorator


@step("create_sample")
def step_create_sample(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    headers: Headers,
) -> "CreateSampleResponse":
    """Create a sample using the API."""

    payload = mappers.sample_to_bonsai(sample_info)
    resp = client.create_sample(payload, headers=headers)

    # set sample id in state
    state.sample_id = resp.internal_sample_id

    return resp


@step("add_to_groups")
def step_add_sample_to_groups(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    headers: Headers,
):
    """Assign a sample to one or more groups."""
    internal_sample_id = state.assert_sample_id()

    responses = []
    for group_id in sample_info.groups:
        resp = client.add_samples_to_group(
            group_id, sample_ids=[internal_sample_id], headers=headers
        )
        responses.append(resp)
    return responses


@step("add_reference_genome")
def step_add_reference_genome(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    headers: Headers,
):
    """Associate sample with a reference genome."""
    internal_sample_id = state.assert_sample_id()
    return client.add_reference_genome_to_sample(
        internal_sample_id,
        reference_genome_id=sample_info.reference_genome_id,
        headers=headers,
    )


@step("add_annotation_track")
def step_add_annotation_track(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    track: IgvAnnotationTrack,
    headers: Headers,
):
    """Associate sample with a reference genome."""
    internal_sample_id = state.assert_sample_id()

    # infere file format if not provided
    file_fmt = track.format
    if file_fmt is None:
        suffix = Path(track.uri).suffix.strip('.')
        if suffix not in EXPECTED_SUFFIXES:
            raise ValueError(
                f"Could not infere format of file '{track.uri}', please specify format."
            )
        file_fmt = suffix

    api_input = GenomicResourceInput(
        reference_genome_id=sample_info.reference_genome_id,
        pipeline_run_id=sample_info.pipeline.pipeline_run_id,
        resource_data=[
            AnnotationTrack(
                name=track.name,
                format=file_fmt,
                type=track.type,
                path=track.uri,
                index_path=track.index_uri,
            )
        ],
    )
    return client.add_annotation_track_to_sample(
        internal_sample_id, track=api_input, headers=headers
    )


@step("add_pipeline_run")
def step_add_pipeline_run(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    headers: Headers,
):
    """Add pipeline run metadata to the sample."""
    run_info = mappers.sample_info_to_pipeline_run(sample_info)
    internal_sample_id = state.assert_sample_id()
    return client.add_pipeline_run(
        internal_sample_id, pipeline_run=run_info, headers=headers
    )


@step("upload_analysis_results")
def step_upload_analysis_results(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    result: MinimalAnalysisRecord,
    headers: Headers,
    **kwargs,
) -> dict[str, str]:
    """Upload analysis results to the sample."""
    internal_sample_id = state.assert_sample_id()

    run_id = sample_info.pipeline.pipeline_run_id
    payload = mappers.analysis_result_to_upload_payload(
        internal_sample_id, run_id=run_id, result=result
    )

    # if "force" flag is set, overwrite existing results for the same software;
    # otherwise, skip upload if results already exist
    force = kwargs.get("force", False)
    resp = client.upload_analysis_result(payload, headers=headers, force=force)
    # build data to be stored in the state
    return {
        "analysis_id": resp.analysis_id,
        "pipeline_run_id": run_id,
        "software": resp.software,
        "software_version": resp.software_version,
        "envelopes": resp.envelopes,
    }


@step("add_ska_index")
def step_upload_ska_index(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    headers: Headers,
):
    """Upload an SKA index for a sample."""
    if not sample_info.index_artifacts or not sample_info.index_artifacts.ska_index:
        return None  # no index to upload

    internal_sample_id = state.assert_sample_id()

    return client.upload_ska_index(
        internal_sample_id,
        index_path=str(sample_info.index_artifacts.ska_index),
        headers=headers,
    )


@step("add_sourmash_signature")
def step_upload_sourmash_signature(
    client: BonsaiApiClient,
    sample_info: ParsedSampleResults,
    state: UploadState,
    *,
    headers: Headers,
):
    """Upload a sourmash signature for a sample."""
    if (
        not sample_info.index_artifacts
        or not sample_info.index_artifacts.sourmash_signature
    ):
        return None  # no index to upload
    internal_sample_id = state.assert_sample_id()

    # read sourmash data
    with sample_info.index_artifacts.sourmash_signature.open("rb") as f:
        return client.upload_sourmash_signature(
            internal_sample_id,
            signature_file=f,
            filename=str(sample_info.index_artifacts.sourmash_signature),
            headers=headers,
    )
