"""Functions for steps in the Bonsai upload pipeline."""

from functools import wraps
from typing import TypeAlias

from prp.pipeline.types import ParsedSampleResults

from . import mappers
from .state_store import UploadState
from .client import BonsaiApiClient


Headers: TypeAlias = dict[str, str]
OpHeaders: TypeAlias = Headers | None


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
        def wrapper(service, client, sample_info, state: UploadState, *, headers: OpHeaders = None, dry_run: bool=False):

            step_name = step_flag
            external_id = state.sample_external_id

            service.reporter.on_step_start(external_id, step_name)

            # Generate headers before the dry_run check for consistent handling and logging.
            headers = headers or {}

            try:
                if dry_run:
                    # assign ID if needed, but do NOT call the API
                    if state.sample_id is None:
                        state.sample_id = "dry-run-sample-id"
                    state.mark(step_name, {"dry_run": True})
                    service.state_store.save(state)
                    service.reporter.on_step_success(external_id, step_name)
                    return None

                # normal execution
                result = fn(client, sample_info, state, headers=headers)
                state.mark(step_name, {"response": result})
                service.state_store.save(state)
                service.reporter.on_step_success(external_id, step_name)
                return result

            except Exception as exc:
                service.reporter.on_step_fail(external_id, step_name, exc)
                raise
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
    client: BonsaiApiClient, _: ParsedSampleResults, state: UploadState, *, headers: Headers
) -> None:
    """Assign a sample to one or more groups."""

    payload = {"s": state.sample_id}
    return client.add_samples_to_group(payload, headers=headers)


@step("add_ska_index")
def step_upload_ska_index(
    client: BonsaiApiClient, sample_info: ParsedSampleResults, state: UploadState, *, headers: Headers
):
    """Upload an SKA index for a sample."""
    return client.upload_ska_index(state.sample_id, index_path=sample_info.ska_index_path, headers=headers)