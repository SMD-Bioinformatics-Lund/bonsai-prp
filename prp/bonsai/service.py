"""Bonsai upload orchestration layer for PRP."""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from prp.bonsai.reportning import SimpleReporter
from prp.pipeline.types import ParsedSampleResults

from .client import BonsaiApiClient
from .state_store import UploadState, UploadStateStore
from . import steps

LOG = logging.getLogger(__name__)


@dataclass
class UploadResult:
    type: str
    sample_id: str
    details: dict[str, Any]


class BonsaiUploadService:
    """Orchistrate multi-step upload of a singel sample to the Bonsai API."""

    def __init__(
        self,
        *,
        client: BonsaiApiClient,
        state_store: UploadStateStore,
        idempotency: bool = True,
        reporter: None = None,
        workflow_id: str | None = None,
        dry_run: bool = False,
    ):
        """
        Args:
            client: An instance of bonsai-libs client (e.g., BonsaiApiClient).
            state_store: Persistent store for per-sample upload state.
            dry_run: If True, do not perform network calls; only log and persist state transitions hypothetically.
        """

        self.client = client
        self.state_store = state_store
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.idempotency = idempotency
        self.reporter = reporter or SimpleReporter()
        self.dry_run = dry_run
    

    def _headers_for(self, step: str, state: UploadState) -> dict[str, str]:
        headers = {
            "X-Workflow-Id": state.workflow_id,
            "X-External-Id": state.sample_external_id,
        }
        if self.idempotency:
            headers["Idempotency-Key"] = f"bonsai-prp/{state.workflow_id}/{state.sample_external_id}/{step}"
        return headers


    # ---- Public API ----

    def upload_sample(self, results: ParsedSampleResults) -> UploadResult:
        """Upload a single sample to Bonsai from a parsed manifest with checkpoint and resume."""
        STEPS = [
            ("sample_created", steps.step_create_sample),
            ("add_to_groups", steps.step_add_sample_to_groups),
        ]

        external_id = results.sample_id
        state = self.state_store.load(self.workflow_id, external_id) or UploadState(
            workflow_id=self.workflow_id, sample_external_id=external_id
        )

        # Notify if resuming
        if state.steps:
            self.reporter.on_resume(external_id, list(state.steps.keys()))

        LOG.info(
            "Uploading sample ext_id=%s (workflow=%s)", external_id, self.workflow_id
        )
        # run steps
        for step_flag, step_fn in STEPS:
            if state.is_done(step_flag):
                self.reporter.on_step_skip(external_id, step_flag)
                continue

            headers = self._headers_for(step_flag, state)

            # apply the step
            step_fn(self, self.client, results, state, headers=headers, dry_run=self.dry_run)

        return state
