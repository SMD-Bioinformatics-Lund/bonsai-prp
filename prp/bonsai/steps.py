"""Functions for steps in the Bonsai upload pipeline."""

from functools import wraps
from typing import Any, Callable, TypeAlias

from prp.pipeline.types import MinimalAnalysisRecord, ParsedSampleResults

from . import mappers
from .state_store import UploadState
from .client import BonsaiApiClient


Headers: TypeAlias = dict[str, str]
OpHeaders: TypeAlias = Headers | None

STEP_REGISTRY: dict[str, Callable[[], Any]] = {}


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
            service, client, sample_info, 
            state: UploadState, *, headers: OpHeaders = None, 
            dry_run: bool=False, substep: str | None = None, **kwargs):

            dynamic_id = f"{step_flag}:{substep}" if substep else step_flag
            external_id = state.sample_external_id

            service.reporter.on_step_start(external_id, dynamic_id)

            # Generate headers before the dry_run check for consistent handling and logging.
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
                result = fn(client, sample_info, state, headers=headers)
                state.mark(dynamic_id, {"response": result})
                service.state_store.save(state)
                service.reporter.on_step_success(external_id, dynamic_id)
                return result

            except Exception as exc:
                service.reporter.on_step_fail(external_id, dynamic_id, exc)
                raise

        STEP_REGISTRY[step_flag] = wrapper  # register the step function for potential dynamic use
        return wrapper
    return decorator


@step("create_sample")
def step_create_sample(
    client: BonsaiApiClient, sample_info: ParsedSampleResults, _: UploadState, *, headers: Headers
    ) -> None:
    """Create a sample using the API."""

    payload = mappers.sample_to_bonsai(sample_info)
    return client.create_sample(payload, headers=headers)


@step("add_to_groups")
def step_add_sample_to_groups(
    client: BonsaiApiClient, sample_info: ParsedSampleResults, state: UploadState, *, headers: Headers
) -> None:
    """Assign a sample to one or more groups."""

    responses = []
    for group_id in sample_info.groups:
        resp = client.add_samples_to_group(group_id, sample_ids=[state.sample_id], headers=headers)
        responses.append(resp)
    return responses


@step("add_pipeline_run")
def step_add_pipeline_run(
    client: BonsaiApiClient, sample_info: ParsedSampleResults, state: UploadState, *, headers: Headers
) -> None:
    """Add pipeline run metadata to the sample."""
    run_info = mappers.sample_info_to_pipeline_run(sample_info)
    return client.add_pipeline_run(state.sample_id, pipeline_run=run_info, headers=headers)


@step("upload_analysis_results")
def step_upload_analysis_results(
    client: BonsaiApiClient, _: ParsedSampleResults, state: UploadState, 
    *, result: MinimalAnalysisRecord, headers: Headers, substep: str | None = None
) -> None:
    """Upload analysis results to the sample."""
    return client.add_analysis_result(state.sample_id, result, headers=headers)


@step("add_ska_index")
def step_upload_ska_index(
    client: BonsaiApiClient, sample_info: ParsedSampleResults, state: UploadState, *, headers: Headers
):
    """Upload an SKA index for a sample."""
    if not sample_info.index_artifacts or not sample_info.index_artifacts.ska_index:
        return None  # no index to upload

    return client.upload_ska_index(
        state.sample_id, index_path=sample_info.index_artifacts.ska_index, headers=headers)


@step("add_sourmash_signature")
def step_upload_sourmash_signature(
    client: BonsaiApiClient, sample_info: ParsedSampleResults, state: UploadState, *, headers: Headers
):
    """Upload a sourmash signature for a sample."""
    if not sample_info.index_artifacts or not sample_info.index_artifacts.sourmash_signature:
        return None  # no index to upload

    return client.upload_sourmash_signature(
        state.sample_id, index_path=sample_info.index_artifacts.sourmash_signature, headers=headers)
