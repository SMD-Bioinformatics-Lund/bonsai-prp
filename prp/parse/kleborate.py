"""Parse Kleborate results.

Documentation: https://kleborate.readthedocs.io/en/latest/index.html
"""

import csv
import logging
import re
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, TextIO, TypeAlias

from prp.models.base import ParserOutput
from prp.models.hamronization import HamronizationEntries, HamronizationEntry
from prp.models.kleborate import (
    KleborateKaptiveLocus,
    KleborateKaptiveTypingResult,
    KleborateMlstLikeResults,
    KleborateQcResult,
    KleborateVirulenceIndex,
    KleborateVirulenceScore,
    KleboreateSppResult,
    KleborateSppIndex,
    KleborateAmrIndex,
    KleborateAmrScoreIndex,
    KleborateQcIndex,
    KleborateTypingIndex
)
from prp.models.amrfinder import AmrFinderResistanceGene, AmrFinderVariant
from prp.models.phenotype import (
    AnnotationType,
    ElementAmrSubtype,
    PhenotypeInfo,
    SequenceStrand,
    VariantSubType,
    VariantType,
)
from prp.models.constants import ElementType
from prp.models.qc import QcSoftware
from prp.models.typing import TypingResultMlst

LOG = logging.getLogger(__name__)


class PresetName(StrEnum):
    """What the species presets are called in the output."""

    KPSC = "klebsiella_pneumo_complex"
    EC = "escherichia"


# Types
Numeric: TypeAlias = int | float
JSONLike: TypeAlias = None | str | Numeric | list["JSONLike"] | dict[str, "JSONLike"]
PercentMode: TypeAlias = Literal["fraction", "percent"]

# Regexes
_PERCENT_RE = re.compile(r"\s*(-?\d+(?:\.\d+)?)\s*%")
_FLOAT_RE = re.compile(r"\s*-?\d+\.\d+\s*")
_INT_RE = re.compile(r"\s*-?\d+\s*")
_HGVS_PROTEIN_RE = re.compile(r"p\.([A-Za-z]+)(\d+)([A-Za-z]+)")
_HGVS_NUCLEOTIDE_RE = re.compile(r"c\.([A-Za-z]+)(\d+)([A-Za-z]+)")


def _normalize_scalar(
    s: str | None,
    percent_mode: PercentMode = "fraction",
    null_values: list[str] = ["-"],
) -> JSONLike:
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


def _normalize_cell(
    raw: str | None,
    percent_mode: PercentMode = "fraction",
    null_values: list[str] = ["-"],
) -> JSONLike:
    """Normalize one cell:
    - Split by ';' into a list if present.
    - Normalize each token via _normalize_scalar.
    - If splits to one item, return the item (not a list).
    - If the cell is empty/None or in null_values, return None
    """
    if raw is None:
        return None

    # check if cell is a list of values
    if ";" in raw:
        parts = [p.strip() for p in raw.split(";")]
        normed = [
            _normalize_scalar(p, percent_mode=percent_mode, null_values=null_values)
            for p in parts
        ]
        if not normed:
            return None

        return normed
    else:
        return _normalize_scalar(
            raw, percent_mode=percent_mode, null_values=null_values
        )


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


def parse_kleborate_output(
    source: TextIO, primary_key: str | None = "strain"
) -> dict[str, Any]:
    """Read and serialize kleborate results as a dicitonary."""
    delimiter = "\t"
    reader = csv.reader(source, delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return {}

    header = rows[0]
    # pre-compute header paths
    header_paths: list[list[str]] = [h.split("__") for h in header]

    result: dict[str, JSONLike] = {}
    for i, row in enumerate(rows[1:], start=1):
        # skip empty lines
        if not any(cell.strip() for cell in row if cell is not None):
            continue

        # Determine sample id
        if primary_key and primary_key in header:
            pk_idx = header.index(primary_key)
            row_key = row[pk_idx].strip() if pk_idx < len(row) else None or f"row_{i}"
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


def _mlst_like_formatter(
    d: dict[str, Any],
    lineage_key: str | None,
    st_key: str,
    qc_keys: list[str],
    schema_name: str,
) -> KleborateMlstLikeResults:
    """Structure MLST-like typing data.

    Note: Qc keys are omitted until the data format allows for generic information.
    """
    typing_result = d.get(schema_name, {})
    # sanity check input
    if not lineage_key:
        raise RuntimeError("Lineage key must be set, check definition")

    if lineage_key not in typing_result:
        raise ValueError(
            f"Lineage key: {lineage_key} not found in data, check definition"
        )

    lineage = (
        "; ".join(typing_result[lineage_key]) if isinstance(typing_result[lineage_key], list) else typing_result[lineage_key]
    )

    if st_key not in typing_result:
        raise ValueError(
            f"Sequence type key: {lineage_key} not in data, check definition"
        )

    if isinstance(typing_result[st_key], str):
        try:
            sequence_type = int(typing_result[st_key])
        except ValueError:
            sequence_type = typing_result[st_key]
    else:
            sequence_type = typing_result[st_key]

    # buld allele list, skip lineage, st, and qc
    skip_keys: list[str] = [lineage_key, st_key, *qc_keys]
    alleles = {key: val for key, val in typing_result.items() if key not in skip_keys}

    # TODO add QC metrics to output
    return KleborateMlstLikeResults(
        lineage=lineage, sequenceType=sequence_type, alleles=alleles, scheme=schema_name
    )


def _format_mlst_like_typing(
    result: dict[str, Any], version: str
) -> list[KleborateTypingIndex]:
    """Generic MLST-like formatter.

    lineage_key: str
    st_key: str
    qc_keys = []
    alleles is the rest
    """
    mlst_like_typing_schemas: dict[str, Any] = {
        "abst": {
            "lineage_key": "Aerobactin",
            "st_key": "AbST",
            "qc_keys": ["spurious_abst_hits"],
        },
        "cbst": {
            "lineage_key": "Colibactin",
            "st_key": "CbST",
            "qc_keys": ["spurious_clb_hits"],
        },
        "rmst": {
            "lineage_key": "RmpADC",
            "st_key": "RmST",
            "qc_keys": ["spurious_rmst_hits"],
        },
        "smst": {
            "lineage_key": "Salmochelin",
            "st_key": "SmST",
            "qc_keys": ["spurious_smst_hits"],
        },
        "ybst": {
            "lineage_key": "Yersiniabactin",
            "st_key": "YbST",
            "qc_keys": ["spurious_ybt_hits"],
        },
    }

    typing_result: list[KleborateTypingIndex] = []
    for name, schema_def in mlst_like_typing_schemas.items():
        try:
            res = _mlst_like_formatter(result, schema_name=name, **schema_def)
            out = KleborateTypingIndex(version=version, result=res)
            typing_result.append(out)
        except RuntimeError as exc:
            LOG.error(f"Critial Kleborate parser error; {exc}")
            raise
        except ValueError as exc:
            LOG.error(f"Could not parse {name} typing; skipping... err: {exc}")
    return typing_result


def _format_mlst_typing(result: dict[str, Any], schema_name: str) -> TypingResultMlst:
    """Format mlst typing"""
    alleles = {}
    return TypingResultMlst(scheme=schema_name, sequenceType=4242, alleles=alleles)


def _parse_qc(result: dict[str, JSONLike], version: str) -> KleborateQcIndex:
    contig_stats = result.get("general", {}).get("contig_stats")
    if contig_stats:
        res = KleborateQcResult(
            n_contigs=contig_stats["contig_count"],
            n50=contig_stats["N50"],
            largest_contig=contig_stats["largest_contig"],
            total_length=contig_stats["total_size"],
            ambigious_bases=True if contig_stats["ambiguous_bases"] == "yes" else "no",
            qc_warnings=contig_stats["QC_warnings"],
        )
        return KleborateQcIndex(software=QcSoftware.KLEBORATE, version=version, result=res)


def _parse_kaptive(d: dict[str, JSONLike], version: str) -> KleborateTypingIndex:
    """Parse kaptive results in Kleborate."""

    def _fmt_res(
        d: dict[str, JSONLike], type: Literal["K", "O"]
    ) -> KleborateKaptiveLocus:
        return KleborateKaptiveLocus(
            locus=d[f"{type}_locus"],
            type=d[f"{type}_type"],
            identity=float(d[f"{type}_locus_identity"]),
            confidence=d[f"{type}_locus_confidence"].lower(),
            problems=d[f"{type}_locus_problems"],
            missing_genes=d[f"{type}_Missing_expected_genes"],
        )

    return KleborateTypingIndex(
        version=version,
        result=KleborateKaptiveTypingResult(
            k_type=_fmt_res(d, "K"), o_type=_fmt_res(d, "O")
        ),
    )


def format_kleborate_output(
    result: dict[str, JSONLike], version: str
) -> list[ParserOutput]:
    """Format raw output to PRP data model.

    It takes a nested dictionary as input where the nesting defines the categories.
    """
    formatted: list[ParserOutput] = []
    # parse qc if there are quality metrics
    if (general_info := result.get("general")) and isinstance(general_info, dict):
        if "contig_stats" in general_info:
            formatted.append(
                ParserOutput(target_field="qc", data=_parse_qc(result, version))
            )

    if (entb_res := result.get("enterobacterales")) and isinstance(entb_res, dict):
        # add species prediction
        raw_spp = entb_res.get("species", {})
        spp_pred = KleboreateSppResult(
            scientificName=raw_spp.get("species", "unknown"),
            match=raw_spp.get("species_match"),
        )
        idx = KleborateSppIndex(result=spp_pred)
        formatted.append(ParserOutput(target_field="species_prediction", data=idx))

    # parse various typing methods
    if "klebsiella" in result:
        formatted.extend(
            [
                ParserOutput(target_field="typing_result", data=idx)
                for idx in _format_mlst_like_typing(
                    result["klebsiella"], version=version
                )
            ]
        )
    # Parse preset specific fields
    if (preset_results := result.get(PresetName.KPSC, {})) and isinstance(
        preset_results, dict
    ):
        # parse mlst
        # KoSC -> pubmlst
        # KpSC -> pasteur
        # if (mlst_res := preset_results.get("mlst", {})) and isinstance(mlst_res, dict):
        #     idx = _format_mlst_typing(preset_results, schema_name="pasteur")
        #     formatted.append(ParserOutput(target_field="typing_result", data=idx))
        # parse virulence
        if (vir_score := preset_results.get("virulence_score", {})) and isinstance(
            vir_score, dict
        ):
            idx = KleborateVirulenceIndex(
                version=version,
                type=ElementType.VIR,
                result=KleborateVirulenceScore(
                    score=int(vir_score["virulence_score"]),
                    spurious_hits=vir_score["spurious_virulence_hits"],
                ),
            )
            formatted.append(ParserOutput(target_field="element_type_result", data=idx))
        # parse kapsule typing
        if (kaptive_res := preset_results.get("kaptive", {})) and isinstance(
            kaptive_res, dict
        ):
            formatted.append(
                ParserOutput(
                    target_field="typing_result",
                    data=_parse_kaptive(kaptive_res, version),
                )
            )
    if (preset_results := result.get(PresetName.EC, {})) and isinstance(
        preset_results, dict
    ):
        if (mlst_res := preset_results.get("mlst", {})) and isinstance(mlst_res, dict):
            pass
            # Ecoli -> both
    return formatted


def _get_hamr_phenotype(record: HamronizationEntry) -> PhenotypeInfo | None:
    """Get phenotypic info from hamronization entry."""
    if record.drug_class is not None:
        return PhenotypeInfo(
            type=ElementType.AMR,
            name=record.drug_class,
            group=record.drug_class,
            annotation_type=AnnotationType.TOOL,
        )


def _convert_strand_orientation(orientation: str | None) -> SequenceStrand | None:
    """Convert hAMRonization strand orientation to a SequenceStrand enum."""
    forward_notations: list[str] = ['+', 'sense']
    reverse_notations: list[str] = ['-', 'antisense']
    if orientation in forward_notations:
        return SequenceStrand.FORWARD
    if orientation in reverse_notations:
        return SequenceStrand.REVERSE
    return None


def hamronization_to_restance_entry(
    entries: HamronizationEntries,
) -> KleborateAmrIndex:
    """Convert hamronization formatted data to a PRP structured record."""
    res_genes: list[AmrFinderResistanceGene] = []
    res_variants: list[AmrFinderVariant] = []
    sw_version: str = entries[0].analysis_software_version
    entry: HamronizationEntry
    for row_no, entry in enumerate(entries, start=1):
        q_start = entry.input.gene_start if entry.input.gene_start else 0
        q_end = entry.input.gene_stop if entry.input.gene_stop else 0
        strand = _convert_strand_orientation(entry.strand_orientation)
        if "gene" in entry.genetic_variation_type.lower():
            # build gene entry
            pheno = _get_hamr_phenotype(entry)
            rec = AmrFinderResistanceGene(
                gene_symbol=entry.gene_symbol,
                sequence_name=entry.gene_name,
                element_type=ElementType.AMR,
                element_subtype=ElementAmrSubtype.AMR,
                contig_id=entry.input.sequence_id or entry.input.file_name,
                query_start_pos=q_start,
                query_end_pos=q_end,
                strand=strand,
                ref_start_pos=entry.reference.gene_start,
                ref_end_pos=entry.reference.gene_stop,
                target_length=entry.reference.gene_length,
                method=entry.analysis_software_name,
                identity=entry.sequence_identity,
                coverage=entry.coverage_percentage,
                phenotypes=[pheno] if pheno else [],
            )
            res_genes.append(rec)
        elif "variant" in entry.genetic_variation_type.lower() or "mutation" in entry.genetic_variation_type.lower():
            variant_info = {}
            if entry.protein_mutation:
                if (match := re.fullmatch(_HGVS_PROTEIN_RE, entry.protein_mutation)) and match:
                    ref, _, alt = match.groups()
                    variant_info['ref_aa'] = ref
                    variant_info['alt_aa'] = alt
            if entry.nucleotide_mutation:
                if (match := re.fullmatch(_HGVS_NUCLEOTIDE_RE, entry.nucleotide_mutation)) and match:
                    ref, _, alt = match.groups()
                    variant_info['ref_nt'] = ref
                    variant_info['alt_nt'] = alt
            rec = AmrFinderVariant(
                id=row_no,
                gene_symbol=entry.gene_symbol,
                variant_type=VariantType.INDEL,
                variant_subtype=VariantSubType.DELETION,
                contig_id=entry.input.sequence_id or entry.input.file_name,
                query_start_pos=q_start,
                query_end_pos=q_end,
                start=entry.reference.gene_start or 0,
                end=entry.reference.gene_stop or 0,
                identity=entry.sequence_identity or -1,
                depth=entry.coverage_depth,
                coverage=entry.coverage_percentage or -1,
                frequency=entry.variant_frequency,
                passed_qc=None,
                confidence=None,
                method="kleborate",
                strand=strand,
                **variant_info
            )
            res_variants.append(rec)
        else:
            LOG.warning(
                f"Could not determine wether entry {row_no} is a gene or variant",
                entry.genetic_variation_type,
            )
    return KleborateAmrIndex(
        version=sw_version,
        type=ElementType.AMR,
        result=ElementTypeResult(variants=res_variants, genes=res_genes),
    )


def parse_kleborate_v3(
    path: Path,
    version: str,
    encoding: str = "utf-8",
    hamronization_entries: HamronizationEntries | None = None,
):
    """Parse Kleborate v3 results to PRP format.

    https://kleborate.readthedocs.io/en/latest/index.html#
    """
    parser_results: list[ParserOutput] = []
    with path.open(encoding=encoding) as inpt:
        results = parse_kleborate_output(inpt)

        # structure analysis result to prp format
        for _, result in results.items():
            parser_results.extend(format_kleborate_output(result, version))

    # optionally add resistance determinants from hAMRonization output
    if hamronization_entries:
        idx = hamronization_to_restance_entry(hamronization_entries)
        parser_results.append(
            ParserOutput(target_field="element_type_result", data=idx)
        )
    return parser_results
