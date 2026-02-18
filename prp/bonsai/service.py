"""Bonsai upload orchestration layer for PRP."""

import json
import logging
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prp.bonsai.reportning import SimpleReporter
from prp.pipeline.types import ParsedSampleResults

from . import mappers
from .client import BonsaiApiClient

LOG = logging.getLogger(__name__)


@dataclass
class UploadResult:
    type: str
    sample_id: str
    details: dict[str, Any]


@dataclass
class UploadState:
    """Durable state for a single sample upload."""

    workflow_id: str
    sample_external_id: str  # stable external key (e.g., lims_id or composite key)
    # server identifiers
    sample_id: str | None = None
    # step booleans and optional details
    steps: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())

    def mark(self, step: str, value: Any = True) -> None:
        self.steps[step] = value
        self.updated_at = _now_iso()

    def is_done(self, step: str) -> bool:
        return bool(self.steps.get(step))


class UploadStateStore:
    """Simple JSON file store for UploadState."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, workflow_id: str, external_id: str) -> Path:
        safe_ext = _safe_name(external_id)
        return self.root / f"{workflow_id}__{safe_ext}.json"

    def load(self, workflow_id: str, external_id: str) -> UploadState | None:
        p = self.path_for(workflow_id, external_id)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return UploadState(**data)

    def save(self, state: UploadState) -> None:
        p = self.path_for(state.workflow_id, state.sample_external_id)
        tmp_fd, tmp_name = tempfile.mkstemp(
            dir=str(self.root), prefix=p.name, suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                json.dump(state.__dict__, fh, ensure_ascii=False, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, p)  # atomic on POSIX
        finally:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:  # best effort cleanup
                LOG.debug("Failed to cleanup tmp file: %s", tmp_name)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in s)[:180]


def _idem_key(workflow_id: str, external_id: str, step: str) -> str:
    return f"bonsai-prp/{workflow_id}/{external_id}/{step}"


class BonsaiUploadService:
    """Orchistrate multi-step upload of a singel sample to the Bonsai API."""

    def __init__(
        self,
        *,
        client: BonsaiApiClient,
        state_store: UploadStateStore,
        idempotency: bool = True,
        reporter: None = None,
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
        self.workflow_id = str(uuid.uuid4())
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
            ("sample_created", step_create_sample),
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
            try:
                step_fn(self.client, results, state, headers=headers, dry_run=self.dry_run)

                # persist state after successful step
                self.state_store.save(state)
                self.reporter.on_step_success(external_id, step_flag)
            except Exception as exc:
                self.reporter.on_step_fail(external_id, step_flag)
                raise

        return state


def step_create_sample(
    client: BonsaiApiClient, manifest_sample: ParsedSampleResults,
    state: UploadState, *, headers: dict[str, str] | None = None, dry_run: bool = False
) -> None:
    """Create a sample using the API."""

    payload = mappers.sample_to_bonsai(manifest_sample)

    LOG.debug(
        "Create sample payload (ext_id=%s): %s",
        state.sample_external_id, payload,
    )

    if dry_run:
        state.sample_id = state.sample_id or "dry-run-sample-id"
        state.mark("sample_created", {"dry_run": True})
        return

    headers = headers or {}
    resp = client.create_sample(payload, headers=headers)
    sample_id = resp.get("sample_id") or resp.get("id")
    if not sample_id:
        LOG.warning("Create sample response missing id; response: %s", resp)

    state.sample_id = sample_id
    state.mark("sample_created", {"response": resp})
