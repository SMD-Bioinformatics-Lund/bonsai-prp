"""Functions for reading delimited files and validating its content."""

from dataclasses import dataclass
import re
from typing import IO, Any, Iterator, Mapping, Sequence, TypeAlias
from pathlib import Path
import csv
import io
import logging

_NULLISH = {None, "", " ", "NA", "N/A", "na", "n/a", ".", "-"}
_TRAILING_ANNOT_RE = re.compile(r"\s*(\([^)]*\)|\[[^\]]*\])\s*$")

LOG = logging.getLogger(__name__)

DelimiterRow: TypeAlias = dict[str, str | None]
DelimiterRows: TypeAlias = list[DelimiterRow]


def _as_text_stream(
    source: IO[bytes] | IO[str],
    *,
    encoding: str = "utf-8",
) -> IO[str]:
    """Return a text stream for a given file-like object (binary or text)."""
    # If it's already a text stream, return as-is
    if isinstance(source, io.TextIOBase):
        return source

    # If it's a binary stream, wrap it
    if isinstance(source, (io.BufferedIOBase, io.RawIOBase)):
        return io.TextIOWrapper(source, encoding=encoding, newline="")

    # Fallback for file-like objects not derived from IOBase:
    # read(0) returns b'' for binary and '' for text.
    peek = source.read(0)  # type: ignore[arg-type]
    if isinstance(peek, (bytes, bytearray)):
        return io.TextIOWrapper(source, encoding=encoding, newline="")  # type: ignore[arg-type]
    return source


def read_delimited(
    source: IO[bytes] | IO[str] | str | Path,
    *,
    delimiter: str = "\t",
    encoding: str = "utf-8",
    has_header: bool = True,
    fieldnames: Sequence[str] | None = None,
    none_values: set[str] | None = None,
    skip_blank_lines: bool = True,
) -> Iterator[DelimiterRow]:
    """
    Read a delimited text file (TSV/CSV) and yield each row as a dict.

    Supports:
      - path-like (str/Path)
      - text streams (IO[str])
      - binary streams (IO[bytes]) e.g. FastAPI UploadFile.file

    Returns raw string values as produced by csv.DictReader.
    """
    if not has_header and fieldnames is None:
        raise ValueError("fieldnames must be provided when has_header=False")

    if isinstance(source, (str, Path)):
        with open(source, "r", encoding=encoding, newline="") as fp:
            yield from read_delimited(
                fp,
                delimiter=delimiter,
                encoding=encoding,
                has_header=has_header,
                fieldnames=fieldnames,
                none_values=none_values,
                skip_blank_lines=skip_blank_lines,
            )
        return

    text_stream = _as_text_stream(source, encoding=encoding)
    # If has_header=False, DictReader will treat the first row as data and use provided fieldnames.
    # If has_header=True and fieldnames=None, DictReader reads header from first row.
    reader = csv.DictReader(text_stream, delimiter=delimiter, fieldnames=fieldnames)

    # If has_header=True AND fieldnames was provided, DictReader will NOT consume header.
    if has_header and fieldnames is not None:
        # Consume one row (the header row) and discard
        next(reader, None)

    none_values = none_values or []

    for row in reader:
        # DictReader may return None keys on malformed rows; ignore those safely
        if None in row:
            row.pop(None, None)

        # Optionally skip blank/empty rows
        if skip_blank_lines and (
            not row or all((v is None or str(v).strip() == "") for v in row.values())
        ):
            continue

        cleaned: dict[str, str | None] = {}
        for key, val in row.items():
            if val is None:
                cleaned[key] = None
                continue
            val = val.strip()
            cleaned[key] = None if val in none_values else val
        yield cleaned


def is_nullish(value: Any, null_values: set[str] = _NULLISH) -> bool:
    """Check if value is a null value."""
    if value is None:
        return True
    if isinstance(value, str) and value.lower().strip() in null_values:
        return True
    return False


def normalize_nulls(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert empty strings to None and preserve other values."""
    out: dict[str, Any] = {}
    for key, val in row.items():
        if is_nullish(val):
            out[key] = None
        else:
            out[key] = val
    return out


@dataclass(frozen=True)
class FieldValidationResult:
    """Result of validated fields."""

    missing: set[str]
    extra: set[str]
    resolved: dict[str, str] | None = None


def validate_fields(
    row: Mapping[str, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
    strict: bool = False,
) -> FieldValidationResult:
    """Validate fields that mandatory fields are present in the data."""
    cols = set(row.keys())
    optional = optional or set()

    missing = required - cols
    allowed = required | optional
    extra = (cols - allowed) if strict else set()

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}; got: {sorted(cols)}"
        )
    if strict and extra:
        raise ValueError(f"Unexpected extra columns: {sorted(extra)}")

    return FieldValidationResult(missing=set(), extra=extra)


def canonical_header(header: str) -> str:
    """
    Remove trailing comment-like blocks: ' (...)' and/or ' [...]' at end of header.
    Repeats removal to handle headers with both (...) and [...] suffixes.
    """
    h = header.strip()
    while True:
        new = _TRAILING_ANNOT_RE.sub("", h).strip()
        if new == h:
            return h
        h = new
