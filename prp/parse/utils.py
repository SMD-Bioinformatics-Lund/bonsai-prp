"""Shared utility functions."""

import csv
import logging
from datetime import datetime
import io
from pathlib import Path
from typing import IO, Any, Iterator, Mapping, Sequence

from prp.models.phenotype import ElementTypeResult, VariantSubType, VariantType
from prp.models.phenotype import SequenceStrand


LOG = logging.getLogger(__name__)


def classify_variant_type(
    ref: str, alt: str, nucleotide: bool = True
) -> tuple[VariantType, VariantSubType]:
    """Classify the type of variant based on the variant length."""
    var_len = abs(len(ref) - len(alt))
    threshold = 50 if nucleotide else 18
    if var_len >= threshold:
        var_type = VariantType.SV
    elif 1 < var_len < threshold:
        var_type = VariantType.INDEL
    else:
        var_type = VariantType.SNV
    if len(ref) > len(alt):
        var_sub_type = VariantSubType.DELETION
    elif len(ref) < len(alt):
        var_sub_type = VariantSubType.INSERTION
    else:
        var_sub_type = VariantSubType.SUBSTITUTION
    return var_type, var_sub_type


def is_prediction_result_empty(result: ElementTypeResult) -> bool:
    """Check if prediction result is emtpy.

    :param result: Prediction result
    :type result: ElementTypeResult
    :return: Retrun True if no resistance was predicted.
    :rtype: bool
    """
    n_entries = len(result.genes) + len(result.variants)
    return n_entries == 0


def get_nt_change(ref_codon: str, alt_codon: str) -> tuple[str, str]:
    """Get nucleotide change from codons

    Ref: TCG, Alt: TTG => tuple[C, T]

    :param ref_codon: Reference codeon
    :type ref_codon: str
    :param str: Alternatve codon
    :type str: str
    :return: Returns nucleotide changed from the reference.
    :rtype: tuple[str, str]
    """
    ref_nt = ""
    alt_nt = ""
    for ref, alt in zip(ref_codon, alt_codon):
        if not ref == alt:
            ref_nt += ref
            alt_nt += alt
    return ref_nt.upper(), alt_nt.upper()


def format_nt_change(
    ref: str,
    alt: str,
    var_type: VariantSubType,
    start_pos: int,
    end_pos: int = None,
) -> str:
    """Format nucleotide change

    :param ref: Reference sequence
    :type ref: str
    :param alt: Alternate sequence
    :type alt: str
    :param pos: Position
    :type pos: int
    :param var_type: Type of change
    :type var_type: VariantSubType
    :return: Formatted nucleotide
    :rtype: str
    """
    match var_type:
        case VariantSubType.SUBSTITUTION:
            fmt_change = f"g.{start_pos}{ref}>{alt}"
        case VariantSubType.DELETION:
            fmt_change = f"g.{start_pos}_{end_pos}del"
        case VariantSubType.INSERTION:
            fmt_change = f"g.{start_pos}_{end_pos}ins{alt}"
        case _:
            fmt_change = ""
    return fmt_change


def reformat_date_str(input_date: str) -> str:
    """Reformat date string into DDMMYY format"""
    # Parse the date string
    try:
        parsed_date = datetime.strptime(input_date, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        parsed_date = datetime.strptime(input_date, "%a %b %d %H:%M:%S %Y %z")

    # Format as DDMMYY
    formatted_date = parsed_date.date().isoformat()
    return formatted_date


def get_db_version(db_version: dict) -> str:
    """Get database version"""
    backup_version = db_version["name"] + "_" + reformat_date_str(db_version["Date"])
    return db_version["commit"] if "commit" in db_version else backup_version


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
) -> Iterator[dict[str, str | None]]:
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
        if skip_blank_lines and (not row or all((v is None or str(v).strip() == "") for v in row.values())):
            continue
        
        cleaned: dict[str, str | None] = {}
        for key, val in row.items():
            if val is None:
                cleaned[key] = None
                continue
            val = val.strip()
            cleaned[key] = None if val in none_values else val
        yield cleaned


def convert_empty_to_none(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert empty strings to None and preserve other values."""
    out: dict[str, Any] = {}
    for key, val in row.items():
        if val == "":
            out[key] = None
        else:
            out[key] = val
    return out


_NULLISH = {None, "", " ", "NA", "N/A", "na", "n/a", ".", "-"}

def _is_nullish(value: Any, null_values: set[str] = _NULLISH) -> bool:
    """Check if value is a null value."""
    if value is None:
        return True
    if isinstance(value, str) and value.lower().strip() in null_values:
        return True
    return False


def safe_int(
        value: Any, 
        *,
        strict: bool = False,
        min_value: int | None = None,
        max_value: int | None = None,
        logger: logging.Logger = LOG
        ) -> int | None:
        """Safely cast a string as an integer."""
        if _is_nullish(value):
            return None
        try:
            if isinstance(value, bool):
                raise ValueError("bool is not a valid int metric")
            if isinstance(value, (int,)):
                out = value
            elif isinstance(value, float):
                # avoid truncating floats, 12.7 -> 12
                if not value.is_integer():
                    raise ValueError(f"non-integer float {value}")
                out = int(value)
            else:
                # strip potential white space
                stringed = str(value).strip()
                out = int(stringed)
            if min_value is not None and out < min_value:
                raise ValueError(f"value {out} < min {min_value}")
            if max_value is not None and out > max_value:
                raise ValueError(f"value {out} > max {max_value}")
            return out
        except Exception as exc:
            reason = str(exc)
            if strict:
                raise ValueError("Failed to cast {value} as an integer: {reason}") from exc
            logger.warning("Bad int cast: value=%s reason=%s", value, reason)
            return None


def safe_float(
        value: Any, 
        *,
        strict: bool = False,
        min_value: int | None = None,
        max_value: int | None = None,
        logger: logging.Logger = LOG
        ) -> float | None:
        """Safely cast a string as a float."""
        if _is_nullish(value):
            return None
        try:
            if isinstance(value, bool):
                raise ValueError("bool is not a valid int metric")
            if isinstance(value, (int, float)):
                out = float(value)
            else:
                # strip potential white space
                stringed = str(value).strip().replace(",", "")  # allow 1,234.5
                out = float(stringed)
            if min_value is not None and out < min_value:
                raise ValueError(f"value {out} < min {min_value}")
            if max_value is not None and out > max_value:
                raise ValueError(f"value {out} > max {max_value}")
            return out
        except Exception as exc:
            reason = str(exc)
            if strict:
                raise ValueError("Failed to cast {value} as a float: {reason}") from exc
            logger.warning("Bad float cast: value=%s reason=%s", value, reason)
            return None


def safe_percent(value: Any, *, logger: logging.Logger = LOG) -> float | None:
    """Accept percentages, 98.7 or '98.7' -> float in [0, 100]."""
    if _is_nullish(value):
            return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.endswith("%"):
            stripped = stripped[:-1].strip()
        value = stripped
    return safe_float(value, min_value=0.0, max_value=100.0, strict=True, logger=logger)


def safe_stand(value: str | int) -> SequenceStrand:
    """Convert sequence strand. [+, 1, sense] -> SequenceStrand enum."""

    # Accept common forward/reverse encodings from bioinformatics tools
    forward_tokens = {
        "+", "1",
        "f", "fwd", "forward",
        "sense", "plus", "pos", "positive",
    }
    reverse_tokens = {
        "-", "-1",
        "r", "rev", "reverse",
        "antisense", "anti-sense", "minus", "neg", "negative",
    }

    # Normalize input
    if isinstance(value, int):
        token = str(value)  # 1 / -1
    else:
        token = value.strip().lower()

    # Some tools may emit " +1 " or " -1 " or "+1"
    # Normalize those into "+"/"-" or "1"/"-1" where possible.
    if token in {"+1", "1+"}:
        token = "1"
    elif token in {"-1", "1-"}:
        token = "-1"

    if value in forward_tokens:
        return SequenceStrand.FORWARD

    if value in reverse_tokens:
        return SequenceStrand.REVERSE
    
    raise ValueError(f"Could not covert {value} to SequenceStrand")
