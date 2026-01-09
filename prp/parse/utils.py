"""Shared utility functions."""

import csv
from datetime import datetime
import io
from pathlib import Path
from typing import IO, Any, Mapping, Tuple

from ..models.phenotype import ElementTypeResult, VariantSubType, VariantType


def classify_variant_type(
    ref: str, alt: str, nucleotide: bool = True
) -> Tuple[VariantType, VariantSubType]:
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


def read_delimited(
    source: IO[bytes] | IO[str] | str | Path,
    *,
    delimiter: str = "\t",
    encoding: str = "utf-8",
):
    """
    Read a delimited text file (TSV/CSV) and yield each row as a dict.

    Supports:
      - path-like (str/Path)
      - text streams (IO[str])
      - binary streams (IO[bytes]) e.g. FastAPI UploadFile.file

    Returns raw string values as produced by csv.DictReader.
    """
    if isinstance(source, (str, Path)):
        with open(source, "r", encoding=encoding, newline="") as fp:
            yield from read_delimited(fp, delimiter=delimiter, encoding=encoding)
        return

    # If it's a binary stream, wrap as text
    if isinstance(getattr(source, "read", None), type(lambda: None)):
        # peek at type by reading attribute 'mode' is unreliable; do safe wrapping:
        if isinstance(source.read(0), (bytes, bytearray)):  # type: ignore[arg-type]
            text_stream: IO[str] = io.TextIOWrapper(source, encoding=encoding, newline="")
        else:
            text_stream = source
    else:
        raise TypeError("source must be a path or file-like object")

    reader = csv.DictReader(text_stream, delimiter=delimiter)
    for row in reader:
        # DictReader may return None keys on malformed rows; ignore those safely
        if None in row:
            row.pop(None, None)
        yield row


def convert_empty_to_none(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert empty strings to None and preserve other values."""
    out: dict[str, Any] = {}
    for key, val in row.items():
        if val == "":
            out[key] = None
        else:
            out[key] = val
    return out
