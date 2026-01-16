"""Functions related to setting result envelopes and their content."""

from typing import Any, Callable

from prp.models.base import ResultEnvelope
from prp.models.enums import ResultStatus

EmptyPredicate = Callable[[Any], bool]


def default_empty_predicate(value: Any) -> bool:
    """Generic tester if result is empty."""
    if value is None:
        return True
    if value == "" or value == [] or value == {}:
        return True
    return False


def envelope_from_value(
        value: Any,
        *,
        empty_predicate: EmptyPredicate = default_empty_predicate,
        reason: str | None = None,
        meta: dict[str, Any] | None = None
    ) -> ResultEnvelope:
    """Create a PARSED/ EMPTY envelope based on the provided result."""

    status = ResultStatus.EMPTY if empty_predicate(value) else ResultStatus.PARSED
    return ResultEnvelope(status=status, value=value, reason=reason, meta=meta or {})


def envelope_error(reason: str, *, meta: dict[str, Any] | None = None) -> ResultEnvelope:
    """Create an envelope that signifies that an error occured."""
    return ResultEnvelope(status=ResultStatus.ERROR, reason=reason, meta=meta or {})


def envelope_absent(reason: str, *, meta: dict[str, Any] | None = None) -> ResultEnvelope:
    """Create an envelope that signifies that the result was absent in the input file."""
    return ResultEnvelope(status=ResultStatus.ABSENT, reason=reason, meta=meta or {})


def envelope_skipped(reason: str = "Omitted by user", *, meta: dict[str, Any] | None = None) -> ResultEnvelope:
    """Create an envelope that signifies that the result was skipped by the user."""
    return ResultEnvelope(status=ResultStatus.SKIPPED, reason=reason, meta=meta or {})
