"""Functions for parsing virulencefinder result."""

import json
import logging
from typing import Any

from prp.exceptions import InvalidDataFormat
from prp.io.json import read_json, require_mapping
from prp.models.phenotype import ElementType, ElementVirulenceSubtype
from prp.models.phenotype import (
    VirulenceElementTypeResult,
    VirulenceGene,
)
from prp.models.sample import MethodIndex
from prp.models.typing import TypingMethod, TypingResultGeneAllele
from prp.models.enums import AnalysisSoftware, AnalysisType
from prp.parse.base import BaseParser, ParseImplOut, ParserInput
from prp.parse.registry import register_parser

LOG = logging.getLogger(__name__)

VIRFINDER = AnalysisSoftware.VIRULENCEFINDER

REQUIRED_FIELDS = {
    "databases", "seq_regions", "software_executions"
}


def parse_vir_gene(
    info: dict[str, Any],
    function: str,
    subtype: ElementVirulenceSubtype = ElementVirulenceSubtype.VIR,
) -> VirulenceGene:
    """Parse virulence gene prediction results."""
    accnr = info.get("ref_acc", None)
    if accnr == "NA":
        accnr = None
    return VirulenceGene(
        # info
        gene_symbol=info["name"],
        accession=accnr,
        sequence_name=function,
        # gene classification
        element_type=ElementType.VIR,
        element_subtype=subtype,
        # position
        ref_start_pos=int(info["ref_start_pos"]),
        ref_end_pos=int(info["ref_end_pos"]),
        ref_gene_length=int(info["ref_seq_length"]),
        alignment_length=int(info["alignment_length"]),
        # prediction
        identity=float(info["identity"]),
        coverage=float(info["coverage"]),
    )


def pick_best_region(regions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the region with highest coverage and identity."""

    if not regions:
        return None
    return max(regions, key=lambda region: (region["coverage"], region["identity"]))

def parse_stx_typing(pred: dict[str, Any]) -> TypingResultGeneAllele | None:
    """Parse STX typing from virulencefinder's output."""

    phenotypes = pred.get("phenotypes", {}) or {}
    seq_regions = pred.get("seq_regions", {}) or {}

    stx_keys = [k for k in phenotypes.keys() if str(k).lower().startswith("stx")]
    if not stx_keys:
        return None

    best_gene: TypingResultGeneAllele | None = None
    best_score: tuple[float, float] = (0.0, 0.0)

    for stx_key in stx_keys:
        pheno = phenotypes.get(stx_key) or {}
        function = pheno.get("function") or ""
        region_keys = pheno.get("seq_regions") or []
        regions = [seq_regions.get(k) for k in region_keys if seq_regions.get(k)]
        best_region = pick_best_region(regions)
        if not best_region:
            continue

        gene = parse_vir_gene(best_region, function=function)
        score = (float(gene.identity or 0.0), float(gene.coverage or 0.0))
        if score > best_score:
            best_score = score
            best_gene = TypingResultGeneAllele(**gene.model_dump())

    return best_gene


def parse_virulence_block(pred: dict[str, Any]) -> VirulenceElementTypeResult:
    """Parse virulencefinder virulence prediction results."""

    vir_genes: list[VirulenceGene] = []
    phenotypes = pred.get("phenotypes", {}) or {}
    seq_regions = pred.get("seq_regions", {}) or {}

    for _, pheno in phenotypes.items():
        function = pheno.get("function") or ""
        ref_dbs = pheno.get("ref_database") or []

        # skip stx typing results
        if any("stx" in str(db).lower() for db in ref_dbs):
            continue

        subtype = ElementVirulenceSubtype.VIR
        if any("toxin" in str(db).lower() for db in ref_dbs):
            subtype = ElementVirulenceSubtype.TOXIN

        region_keys = pheno.get("seq_regions") or []
        regions = [seq_regions.get(k) for k in region_keys if seq_regions.get(k)]
        for info in regions:
            vir_genes.append(parse_vir_gene(info, function=function, subtype=subtype))

    # stable sort, handle None safely if coverage can be None
    vir_genes.sort(key=lambda g: (g.gene_symbol or "", g.coverage if g.coverage is not None else -1.0))

    return VirulenceElementTypeResult(genes=vir_genes, variants=[], phenotypes={})


@register_parser(VIRFINDER)
class VirulenceFinderParser(BaseParser):
    """VirulenceFinder parser."""

    software = VIRFINDER
    parser_name = "VirulenceFinderParser"
    parser_version = "1"
    schema_version = "1"
    produces = {AnalysisType.VIRULENCE, AnalysisType.STX}

    def _parse_impl(
        self,
        source: ParserInput,
        *,
        want: set[AnalysisType],
        strict: bool = False,
        **kwargs: Any,
    ) -> ParseImplOut:
        """Parse virulence finder resuls."""
        try:
            raw = read_json(source)
            raw = require_mapping(raw, what="<root>")
            for field in REQUIRED_FIELDS:
                require_mapping(raw.get(field), what=field)

        except TypeError as exc:
            self.log_error("Failed to read SerotypeFinder JSON", error=str(exc))
            if strict:
                raise
            return {}
        except InvalidDataFormat as exc:
            self.log_error("Failed to read/validate VirulenceFinder JSON", error=str(exc))
            if strict:
                raise
            return {}

        out: dict[AnalysisType, Any] = {}

        if AnalysisType.VIRULENCE in want:
            out[AnalysisType.VIRULENCE] = parse_virulence_block(raw)

        if AnalysisType.STX in want:
            out[AnalysisType.STX] = parse_stx_typing(raw)

        # Summary logging
        if AnalysisType.VIRULENCE in out:
            self.log_info("VirulenceFinder parsed virulence", genes=len(out[AnalysisType.VIRULENCE].genes))
        if AnalysisType.STX in out:
            self.log_info("VirulenceFinder parsed stx", has_hit=out[AnalysisType.STX] is not None)

        return out
