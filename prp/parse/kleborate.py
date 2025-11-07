"""Parse Kleborate results.

Documentation: https://kleborate.readthedocs.io/en/latest/index.html
"""

import csv
import re
from pathlib import Path
from typing import Any, TextIO, Literal, TypeAlias

from prp.models.base import ParserOutput
from prp.models.qc import QcSoftware
from prp.models.typing import TypingResultMlst
from prp.models.kleborate import KleborateMethodIndex, KleborateQcResult, KleboreateSppResult

# Types
Numeric: TypeAlias = int | float
JSONLike: TypeAlias = None | str | Numeric | list["JSONLike"] | dict[str, "JSONLike"]
PercentMode: TypeAlias = Literal["fraction", "percent"]

# Regexes
_PERCENT_RE = re.compile(r"\s*(-?\d+(?:\.\d+)?)\s*%")
_FLOAT_RE = re.compile(r"\s*-?\d+\.\d+\s*")
_INT_RE = re.compile(r"\s*-?\d+\s*")


def _normalize_scalar(s: str | None, percent_mode: PercentMode = "fraction", null_values: list[str] = ["-"]) -> JSONLike:
    """Normalize stringed value to python type.
    
    percent_mode == "fraction" -> (0-1)
    percent_mode == "percent" -> (0-100)
    """
    if s is None:
        return None
    
    s = s.strip()
    if not s or s in null_values:
        return None

    # Convert percentages (numeric + %)
    match = _PERCENT_RE.fullmatch(s)
    if match:
        val = float(match.group(1))
        return (val / 100) if percent_mode == "fraction" else val

    if _FLOAT_RE.fullmatch(s):
        return float(s)
    
    if _INT_RE.fullmatch(s):
        return int(s)
    return s
    

def _normalize_cell(raw: str | None, percent_mode: PercentMode = 'fraction', null_values: list[str] = ['-']) -> JSONLike:
    """Normalize one cell:
      - Split by ';' into a list if present.
      - Normalize each token via _normalize_scalar.
      - If splits to one item, return the item (not a list).
      - If the cell is empty/None or in null_values, return None
    """
    if raw is None:
        return None

    # check if cell is a list of values
    if ';' in raw:
        parts = [p.strip() for p in raw.split(';')]
        normed = [_normalize_scalar(p, percent_mode=percent_mode, null_values=null_values) for p in parts]
        if not normed:
            return None

        return normed
    else:
        return _normalize_scalar(raw, percent_mode=percent_mode, null_values=null_values)


def _set_nested(d: dict[str, Any], path: list[str], value: Any) -> dict[str, Any]:
    """Set value in a nested dict according to path."""
    if not path:
        return
    
    key = path[0]
    # create new node if node has not yet been added
    node: dict[str, Any] | None = d.get(key)
    if not isinstance(node, dict):
        node = {}
        d[key] = node

    if len(path) > 1:
        d[key] = _set_nested(node, path[1:], value)
    else:
        d[key] = value
    return d


def parse_kleborate_output(source: TextIO, encoding: str = "utf-8", primary_key: str | None = "strain") -> dict[str, Any]:
    """Read and serialize kleborate results as a dicitonary.
    
    """
    delimiter = '\t'
    reader = csv.reader(source, delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return {}

    header = rows[0]
    # pre-compute header paths
    header_paths: list[list[str]] = [h.split('__') for h in header]

    result: dict[str, JSONLike] = {}
    for i, row in enumerate(rows[1:], start=1):
        # skip empty lines
        if not any(cell.strip() for cell in row if cell is not None):
            continue

        # Determine sample id 
        if primary_key and primary_key in header:
            pk_idx = header.index(primary_key)
            row_key = (row[pk_idx].strip() if pk_idx < len(row) else None or f"row_{i}")
        else:
            row_key = f"row_{i}"
        
        # create nested json-like structure from header
        # foo__bar__doo -> {'foo': {'bar': {'doo': value}}} 
        nested: dict[str, JSONLike] = {}
        for col_idx, path in enumerate(header_paths):
            # Safeguard that row is as long as the header
            raw_value = row[col_idx] if col_idx < len(row) else None
            value = _normalize_cell(raw_value)
            nested = _set_nested(nested, path, value)
        result[row_key] = nested
    return result


def _format_mlst_like_typing(d: dict[str, Any], lineage_key: str | None, st_key: str, qc_keys: list[str]) -> TypingResultMlst:
    """Structure MLST-like typing data.
    
    Note: Qc keys are omitted until the data format allows for generic information.
    """
    if lineage_key and lineage_key not in d:
        raise ValueError(f"Lineage key: {lineage_key} not found in data, check definition")

    if st_key not in d:
        raise ValueError(f"Sequence type key: {lineage_key} not in data, check definition")

    return TypingResultMlst(scheme="bar")


def _format_mlst_typing(result: dict[str, Any]) -> list[ParserOutput]:
    """Generic MLST-like formatter.
    
    lineage_key: str
    st_key: str
    qc_keys = []
    alleles is the rest
    """
    mlst_like_typing_schemas: dict[str, Any] = {
        'abst': {"lineage_key": "Aerobactin", "st_key": "AbST", "qc_keys": ["spurious_abst_hits"]}, 
        'cbst': {"lineage_key": "Colibactin", "st_key": "CbST", "qc_keys": ["spurious_clb_hits"]}, 
        'rmst': {"lineage_key": "RmpADC", "st_key": "RmST", "qc_keys": ["spurious_rmst_hits"]}, 
        'smst': {"lineage_key": "Salmochelin", "st_key": "SmST", "qc_keys": ["spurious_smst_hits"]}, 
        'ybst': {"lineage_key": "Yersiniabactin", "st_key": "YbST", "qc_keys": ["spurious_ybt_hits"]}
    }
    for schema in mlst_like_typing_schemas:
        pass



def format_kleborate_output(result: dict[str, JSONLike]) -> list[ParserOutput]:
    """Format raw output to PRP data model.
    
    It takes a nested dictionary as input where the nesting defines the categories.
    """
    formatted: list[ParserOutput] = []
    # qc metrics
    contig_stats = result.get('general', {}).get('contig_stats')
    if contig_stats:
        res = KleborateMethodIndex(
            software=QcSoftware.KLEBORATE, 
            version="to_be_added",
            result=KleborateQcResult(
                n_contigs=contig_stats['contig_count'],
                n50=contig_stats['N50'],
                largest_contig=contig_stats['largest_contig'],
                total_length=contig_stats['total_size'],
                ambigious_bases=True if contig_stats['ambiguous_bases'] == 'yes' else 'no',
                qc_warnings=contig_stats['QC_warnings']
            )
        )
        formatted.append(ParserOutput(target_field='qc', data=res))

    if 'enterobacterales' in result:
        # add species prediction
        raw_spp: dict[str, str] = result['enterobacterales'].get('species', dict)
        spp_pred = kleboreatesppresult(
            scientificName=raw_spp.get("species", "unknown"),
            match=raw_spp["species_match"]
        )
        formatted.append(ParserOutput(target_field='species_prediction', data=spp_pred))

    # parse various typing methods
    if 'klebsiella' in result:
        formatted.extend(_format_mlst_typing(result['klebsiella']))
        
    return formatted


def parse_kleborate_v3(path: Path, encoding: str = "utf-8"):
    """Parse Kleborate v3 results to PRP format.

    https://kleborate.readthedocs.io/en/latest/index.html#
    """
    with path.open(encoding=encoding) as inpt:
        results = parse_kleborate_output(inpt)

        # structure analysis result to prp format
        for _, result in results.items():
            format_kleborate_output(result)
