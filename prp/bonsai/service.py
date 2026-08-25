"""Bonsai upload orchestration layer for PRP."""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from bonsai_libs.api_client.bonsai.models import (
    CreateGroupInput,
    CreateReferenceGenomeInput,
    CreateUserInput,
)
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
        ignore_errors: bool = False,
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
        self.ignore_errors = ignore_errors

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

    def ensure_user_exists(self, user_data: CreateUserInput) -> dict[str, Any]:
        """
        Get existing user or create if missing.

        Args:
            user_id: The unique identifier for the user.
            **user_data: Additional user data to pass during creation.

        Returns:
            The user object from the API.
        """
        username = user_data.username
        try:
            LOG.debug("Fetching user: %s", username)
            user = self.client.get_user(username)
            LOG.info("User already exists: %s", username)
            return user
        except ClientError as exc:
            if exc.status == 404:
                LOG.info("Creating new user: %s", username)
                user = self.client.create_user(user_data)
                LOG.info("User created successfully: %s", username)
                return user
            # Re-raise if it's not a 404
            raise

    def ensure_group_exists(self, group_data: CreateGroupInput) -> dict[str, Any]:
        """
        Get existing group or create if missing.

        Args:
            group_id: The unique identifier for the group.
            **group_data: Additional group data to pass during creation.

        Returns:
            The group object from the API.
        """
        group_id = group_data.group_id
        try:
            LOG.debug("Fetching group: %s", group_id)
            group = self.client.get_group(group_id)
            LOG.info("Group already exists: %s", group_id)
            return group
        except ClientError as exc:
            if exc.status == 404:
                LOG.info("Creating new group: %s", group_id)
                group = self.client.create_group(group_data)
                LOG.info("Group created successfully: %s", group_id)
                return group
            # Re-raise if it's not a 404
            raise

    def ensure_reference_genome_exists(
        self, genome_data: CreateReferenceGenomeInput
    ) -> dict[str, Any]:
        """
        Get existing reference gneome or create if missing.

        Returns:
            The reference genome object from the API.
        """
        genomes = []
        try:
            LOG.debug("Fetching reference genomes")
            genomes = self.client.list_reference_genomes()
        except ClientError as exc:
            if exc.status == 404:
                LOG.info("Creating new ref genome")
                genome = self.client.create_reference_genome(genome_data)
                LOG.info("Reference genome created successfully: id=%s", genome["id"])
                return genome

        # check if genomes exist
        for genome in genomes:
            same_name = genome_data.name == genome["name"]
            same_accnr = genome_data.accession == genome["accession"]
            same_organism = genome_data.organism == genome["accession"]
            if same_name and same_accnr and same_organism:
                LOG.info("Reference genome exists: id=%s", genome["id"])
                return genome

        LOG.info("Creating new ref genome")
        genome = self.client.create_reference_genome(genome_data)
        LOG.info("Reference genome created successfully: id=%s", genome["id"])
        return genome

    def upload_sample(
        self, results: ParsedSampleResults, *, force: bool, only: set[str] | None = None
    ) -> UploadResult:
        """Upload a single sample to Bonsai from a manifest.

        When ``only`` is given (a set of software names), restrict the upload to
        the analysis results from those softwares and skip sample creation,
        reference genome, pipeline run, index and annotation-track steps. This
        overwrites just those results on an already-existing sample;
        ``results.sample_id`` must be the sample's existing (internal) Bonsai id.
        Combine with ``force`` to overwrite results that already exist.
        """
        upload_steps = [
            "create_sample",
            "add_reference_genome",
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

        if only:
            # Result-only mode: the sample already exists, so adopt its id directly
            # instead of creating it, and skip every step except result upload.
            state.sample_id = external_id
        else:
            # Phase 1: run fixed steps
            for step_name in upload_steps:
                if state.is_done(step_name):
                    self.reporter.on_step_skip(external_id, step_name)
                    continue

                step_fn = steps.lookup_step(step_name)
                headers = self._headers_for(step_name, state)

                # decorator handles state persistence, error handling, and dry-run logic
                step_fn(
                    self,
                    self.client,
                    results,
                    state,
                    headers=headers,
                    dry_run=self.dry_run,
                    ignore_errors=self.ignore_errors,
                )

            # Phase 2: create annotation tracks
            step_name = "add_annotation_track"
            create_track_fn = steps.lookup_step(step_name)
            for track in results.annotation_tracks:
                substep = track.name  # used for dynamic state key

                # Skip if upload step has been run
                if state.is_done(f"{step_name}:{substep}") and not force:
                    self.reporter.on_step_skip(external_id, f"{step_name}:{substep}")
                    continue

                headers = self._headers_for("upload_analysis_results", state)
                create_track_fn(
                    self,
                    self.client,
                    results,
                    state,
                    track=track,
                    headers=headers,
                    substep=substep,
                    dry_run=self.dry_run,
                    ignore_errors=self.ignore_errors,
                )

        # Warn about requested softwares that aren't present in the manifest, so a
        # typo in --only doesn't silently upload nothing.
        if only:
            available = {r.software for r in results.analysis_results}
            for software in sorted(only - available):
                LOG.warning(
                    "Requested --only software '%s' not found in manifest for %s",
                    software,
                    external_id,
                )

        # Phase 3: upload analysis results
        step_name = "upload_analysis_results"
        upload_analysis_fn = steps.lookup_step(step_name)
        for result in results.analysis_results:
            if only and result.software not in only:
                continue

            if not isinstance(result, MinimalAnalysisRecord):
                LOG.warning(
                    "Skipping upload of result with software=%s due to missing URI",
                    result.software,
                )
                continue

            substep = result.software  # used for dynamic state key

            # Skip if upload step has been run
            if state.is_done(f"{step_name}:{substep}") and not force:
                self.reporter.on_step_skip(external_id, f"{step_name}:{substep}")
                continue

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
                ignore_errors=self.ignore_errors,
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
