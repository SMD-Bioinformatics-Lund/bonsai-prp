"""Bonsai upload orchestration layer for PRP."""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from bonsai_libs.api_client.core.exceptions import ClientError

from prp.bonsai.reportning import SimpleReporter
from prp.pipeline.types import MinimalAnalysisRecord, ParsedSampleResults

from . import steps
from .client import BonsaiApiClient
from .state_store import UploadState, UploadStateStore

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
            dry_run: If True, do not perform network calls;
                    only log and persist state transitions hypothetically.
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
            headers["Idempotency-Key"] = (
                f"bonsai-prp/{state.workflow_id}/{state.sample_external_id}/{step}"
            )
        return headers

    # ---- Public API ----

    def ensure_user_exists(self, user_id: str, **user_data) -> dict[str, Any]:
        """
        Get existing user or create if missing.

        Args:
            user_id: The unique identifier for the user.
            **user_data: Additional user data to pass during creation.

        Returns:
            The user object from the API.
        """
        try:
            LOG.debug("Fetching user: %s", user_id)
            user = self.client.get_user(user_id)
            LOG.info("User already exists: %s", user_id)
            return user
        except ClientError as exc:
            if exc.status == 404:
                LOG.info("Creating new user: %s", user_id)
                user = self.client.create_user(user_id, **user_data)
                LOG.info("User created successfully: %s", user_id)
                return user
            # Re-raise if it's not a 404
            raise

    def ensure_group_exists(self, group_id: str, **group_data) -> dict[str, Any]:
        """
        Get existing group or create if missing.

        Args:
            group_id: The unique identifier for the group.
            **group_data: Additional group data to pass during creation.

        Returns:
            The group object from the API.
        """
        try:
            LOG.debug("Fetching group: %s", group_id)
            group = self.client.get_group(group_id)
            LOG.info("Group already exists: %s", group_id)
            return group
        except ClientError as exc:
            if exc.status == 404:
                LOG.info("Creating new group: %s", group_id)
                group = self.client.create_group(group_id, **group_data)
                LOG.info("Group created successfully: %s", group_id)
                return group
            # Re-raise if it's not a 404
            raise

    def upload_sample(
        self, results: ParsedSampleResults, *, force: bool
    ) -> UploadResult:
        """Upload a single sample to Bonsai from a manifest."""
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
            step_fn(
                self, self.client, results, state, headers=headers, dry_run=self.dry_run
            )

        # Phase 2: upload analysis results
        upload_analysis_fn = steps.lookup_step("upload_analysis_results")
        for result in results.analysis_results:
            if not isinstance(result, MinimalAnalysisRecord):
                LOG.warning(
                    "Skipping upload of result with software=%s due to missing URI",
                    result.software,
                )
                continue

            substep = result.software  # used for dynamic state key
            headers = self._headers_for("upload_analysis_results", state)
            upload_analysis_fn(
                self,
                self.client,
                results,
                state,
                result=result,
                headers=headers,
                substep=substep,
                dry_run=self.dry_run,
                force=force,
            )

        # Build a friendly summary result
        executed = [
            k
            for k, v in state.steps.items()
            if v and not (isinstance(v, dict) and v.get("skipped"))
        ]
        return UploadResult(
            type="success",
            sample_id=state.sample_id or "",
            details={
                "executed_steps": executed,
                "total_steps": len(executed),
                "resume_supported": True,
            },
        )
