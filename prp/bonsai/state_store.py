"""State management for bonsai-prp sample uploads."""

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

LOG = logging.getLogger(__name__)


def _now_iso() -> str:
    """Get current time as ISO string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_dict(data):
    """Recursively convert BaseModel instances in a dict to plain dicts."""

    out = {}
    for k, v in data.items():
        if isinstance(v, BaseModel):
            out[k] = v.model_dump()
        elif isinstance(v, dict):
            out[k] = _normalize_dict(v)
        else:
            out[k] = v
    return out


@dataclass
class UploadState:
    """Durable state for a single sample upload."""

    workflow_id: str
    sample_external_id: str  # stable external key (e.g., lims_id or composite key)

    # server identifiers
    sample_id: str | None = None

    # step booleans and optional details
    steps: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def mark(self, step: str, value: Any = True) -> None:
        """Mark a step as done, optionally with additional details."""

        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        if isinstance(value, dict):
            value = _normalize_dict(value)
        self.steps[step] = value
        self.updated_at = _now_iso()

    def is_done(self, step: str) -> bool:
        """Check if a step is marked as done."""

        return bool(self.steps.get(step))


class UploadStateStore:
    """Simple JSON file store for UploadState."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, workflow_id: str, external_id: str) -> Path:
        """Get the file path for a given workflow and sample external ID."""

        safe_ext = _safe_name(external_id)
        return self.root / f"{workflow_id}__{safe_ext}.json"

    def load(self, workflow_id: str, external_id: str) -> UploadState | None:
        """Load state from JSON file; return None if not found."""

        p = self.path_for(workflow_id, external_id)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return UploadState(**data)

    def save(self, state: UploadState) -> None:
        """Save state to JSON file atomically."""

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


def _safe_name(s: str) -> str:
    """Sanitize a string to be safe for filenames, keeping it reasonably readable."""

    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in s)[:180]


def _idem_key(workflow_id: str, external_id: str, step: str) -> str:
    """Generate a consistent key for idempotent steps."""

    return f"bonsai-prp/{workflow_id}/{external_id}/{step}"
