"""Bonsai upload orchestration layer for PRP."""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from prp.bonsai.reportning import SimpleReporter
from prp.pipeline.types import MinimalAnalysisRecord, ParsedSampleResults

from .client import BonsaiApiClient
from .state_store import UploadState, UploadStateStore
from . import steps

LOG = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Structured result of an upload operation."""

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
        upload_steps = [
            "create_sample", 
            "add_pipeline_run", 
            "add_ska_index", 
            "add_sourmash_signature",
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
        # Phase 1: run fixed steps
        for step_name in upload_steps:
            if state.is_done(step_name):
                self.reporter.on_step_skip(external_id, step_name)
                continue

            step_fn = steps.lookup_step(step_name)
            headers = self._headers_for(step_name, state)

            # decorator handles state persistence, error handling, and dry-run logic
            step_fn(self, self.client, results, state, headers=headers, dry_run=self.dry_run)
        
        # Phase 2: upload analysis results
        upload_analysis_fn = steps.lookup_step("upload_analysis_results")
        for result in results.analysis_results:
            if not isinstance(result, MinimalAnalysisRecord):
                LOG.warning("Skipping upload of analysis result with software=%s due to missing URI", result.software)
                continue

            substep = result.software  # used for dynamic state key
            headers = self._headers_for("upload_analysis_results", state)
            upload_analysis_fn(
                self, self.client, results, state,
                result=result,
                headers=headers,
                substep=substep,
                dry_run=self.dry_run,
            )
        
        # Build a friendly summary result
        executed = [k for k, v in state.steps.items() if v and not (isinstance(v, dict) and v.get("skipped"))]
        return UploadResult(
            type="success",
            sample_id=state.sample_id or "",
            details={
                "executed_steps": executed,
                "total_steps": len(executed),
                "resume_supported": True,
            }
        )
