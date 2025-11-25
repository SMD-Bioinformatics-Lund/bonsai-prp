"""Parse the hAMRonization format.

Kleborate implementation: https://kleborate.readthedocs.io/en/stable/kpsc_modules.html#hamronization-report-for-kleborate
"""

import csv
import logging
import re
from typing import Any, Literal, TextIO, TypeAlias

from prp.models.hamronization import (
    BaseSequenceRecord,
    HamronizationEntry,
    InputSequence,
    ReferenceSequence,
)
from prp.models.metadata import SoupType, SoupVersion

LOG = logging.getLogger(__name__)

HamronizationEntries = list[HamronizationEntry]
PercentMode: TypeAlias = Literal["fraction", "percent"]

# Regexes
_PERCENT_RE = re.compile(r"\s*(-?\d+(?:\.\d+)?)\s*%")
_FLOAT_RE = re.compile(r"\s*-?\d+\.\d+\s*")
_INT_RE = re.compile(r"\s*-?\d+\s*")


def normalize_cell(
    value: str | None,
    percent_mode: PercentMode = "fraction",
    null_values: list[str] = ["-", "NA", ""],
) -> int | float | None | str:
    """Normalize a cell value:
    - Strip whitespace
    - Convert null values to None
    - Convert "XX.XX%" to float (fraction, e.g. "50%" -> 0.5)
    - Convert stringed int/float to correct type
    - Return string otherwise

    percent_mode == "fraction" -> (0-1)
    percent_mode == "percent" -> (0-100)
    """
    if value is None:
        return None
    value = value.strip()
    if value in null_values:
        return None
    # Handle percentages
    match = _PERCENT_RE.fullmatch(value)
    if match:
        val = float(match.group(1))
        return (val / 100) if percent_mode == "fraction" else val

    if _FLOAT_RE.fullmatch(value):
        return float(value)

    if _INT_RE.fullmatch(value):
        return int(value)
    return value


def _get_gene_pos(
    d: dict[str, Any], prefix: Literal["input", "reference"]
) -> BaseSequenceRecord:
    """Get base sequence record info."""
    return BaseSequenceRecord(
        gene_start=d.get(f"{prefix}_gene_start"),
        gene_stop=d.get(f"{prefix}_gene_stop"),
        gene_length=d.get(f"{prefix}_gene_length"),
    )


def _convert_strand_orientation(value: str) -> Literal["+", "-"] | None:
    """Convert strand orientation to + or - for sense and antisense strands."""
    sense_symbols: list[str] = ["+", "sense", "1"]
    antisense_symbols: list[str] = ["-", "antisense", "-1"]

    if value in sense_symbols:
        return "+"
    if value in antisense_symbols:
        return "-"


def get_version(source: TextIO) -> SoupVersion | None:
    """Naive get software and version from a hAMRonization file."""
    LOG.debug("Get analysis software and version from hAMRonization file.")
    # deduplicate versions and entries
    for entry in parse_hamronization(source):
        return SoupVersion(
            name=entry.analysis_software_name,
            version=entry.analysis_software_version,
            type=SoupType.SW,
        )


def parse_hamronization(
    source: TextIO, null_values: list[str] = ["NA", "-"]
) -> HamronizationEntries:
    """Parse harmonization format."""
    delimiter = "\t"
    header = [
        col.strip().lower().replace(" ", "_")
        for col in source.readline().split(delimiter)
    ]
    creader = csv.DictReader(source, fieldnames=header, delimiter=delimiter)

    rows: HamronizationEntries = []
    row: dict[str, str]
    for row in creader:
        # skip strand orientation since it can be - which does not denote null
        clean_row = {
            k: normalize_cell(v, percent_mode="percent")
            for k, v in row.items()
            if k != "strand_orientation"
        }
        input_seq = InputSequence(
            file_name=clean_row.get("input_file_name"),
            sequence_id=clean_row.get("input_sequence_id"),
            **_get_gene_pos(clean_row, "input").model_dump(mode="json"),
        )
        accnr = (
            clean_row.get("reference_accession")
            if clean_row.get("reference_accession")
            else "unknown"
        )
        ref_seq = ReferenceSequence(
            accession=accnr,
            reference_db_id=clean_row.get("reference_database_name"),
            reference_db_version=clean_row.get("reference_database_name"),
            **_get_gene_pos(clean_row, "reference").model_dump(mode="json"),
        )
        # convert strand
        strand_orientation = _convert_strand_orientation(
            clean_row.get("strand_orientation")
        )

        # convert mutation entry. This is specifically for the Kleborate implementation of the specification
        variant_info: dict[str, Any] = {}
        nucleotide_mutations = ("c", "g", "n")
        if (mutation := clean_row.get("mutation")) is not None:
            if isinstance(mutation, str) and mutation.startswith("p."):
                variant_info["protein_mutation"] = mutation
            elif isinstance(mutation, str) and mutation[0] in nucleotide_mutations:
                variant_info["nucleotide_mutation"] = mutation

        gene_symbol = clean_row.get("gene_symbol")
        entry = HamronizationEntry(
            analysis_software_name=clean_row.get("software_name"),
            analysis_software_version=clean_row.get("software_version"),
            input=input_seq,
            reference=ref_seq,
            gene_name=clean_row.get("gene_name") or gene_symbol,
            gene_symbol=gene_symbol,
            strand_orientation=strand_orientation,
            coverage_percentage=clean_row.get("coverage"),
            coverage_depth=clean_row.get("coverage_depth"),
            coverage_ratio=clean_row.get("coverage_ration"),
            sequence_identity=clean_row.get("sequence_identity"),
            drug_class=clean_row.get("drug_class"),
            genetic_variation_type=clean_row.get("genetic_variation_type"),
            **variant_info,
        )
        rows.append(entry)
    return rows
