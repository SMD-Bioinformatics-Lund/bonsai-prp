"""Parse TBprofiler result."""

from typing import Any, Sequence

from prp.io.json import read_json
from prp.models.enums import AnalysisSoftware, AnalysisType
from prp.models.metadata import SoupType, SoupVersion
from prp.models.phenotype import (
    AnnotationType,
    ElementType,
    ElementTypeResult,
    PhenotypeInfo,
)
from prp.models.phenotype import PredictionSoftware as Software
from prp.models.phenotype import TbProfilerVariant, VariantSubType, VariantType
from prp.models.typing import LineageInformation
from prp.parse.base import BaseParser, ParseImplOut, ParserInput

from .utils import get_db_version


def _get_sr_profie(pred: dict[str, Any]) -> dict[str, list[str]]:
    """Get tbprofiler susceptibility/resistance profile."""
    drugs = [
        "ofloxacin",
        "moxifloxacin",
        "isoniazid",
        "delamanid",
        "kanamycin",
        "amikacin",
        "ethambutol",
        "ethionamide",
        "streptomycin",
        "ciprofloxacin",
        "levofloxacin",
        "pyrazinamide",
        "linezolid",
        "rifampicin",
        "capreomycin",
    ]

    resistant: set[str] = set()
    for hit in pred.get("dr_variants", []) or []:
        for drug in hit.get("gene_associated_drugs", []) or []:
            resistant.add(drug)

    susceptible = [drug for drug in drugs if drug not in resistant]
    return {"susceptible": sorted(susceptible), "resistant": sorted(resistant)}


def _parse_variants(pred: dict[str, Any]) -> Sequence[TbProfilerVariant]:
    """Get resistance genes from tbprofiler result."""
    # Find variant caller if present
    variant_caller = None
    for prog in pred.get("pipeline", {}).get("software", []) or []:
        if (prog.get("process") or "").lower() == "variant_calling":
            variant_caller = prog.get("software")
            break

    # tbprofiler report three categories of variants
    # - dr_variants: known resistance variants
    # - qc_fail_variants: known resistance variants failing qc
    # - other_variants: variants not in the database but in genes
    #                   associated with resistance
    results: list[TbProfilerVariant] = []
    var_id = 1
    for result_type in ("dr_variants", "other_variants", "qc_fail_variants"):
        # associated with passed/ failed qc
        passed_qc = result_type != "qc_fail_variants"

        # parse variants
        for hit in pred.get(result_type, []) or []:
            ref_nt = hit.get("ref") or ""
            alt_nt = hit.get("alt") or ""
            is_sv = bool(hit.get("sv"))

            # Determine type based on length change and/ or SV flag
            var_len = abs(len(ref_nt) - len(alt_nt))
            if is_sv or var_len >= 50:
                var_type = VariantType.SV
            elif 1 < var_len < 50:
                var_type = VariantType.INDEL
            else:
                var_type = VariantType.SNV

            # Determine subtype
            if len(ref_nt) == len(alt_nt):
                var_sub_type = VariantSubType.SUBSTITUTION
            elif len(ref_nt) > len(alt_nt):
                var_sub_type = VariantSubType.DELETION
            else:
                var_sub_type = VariantSubType.INSERTION

            results.append(
                TbProfilerVariant(
                    # classificatoin
                    id=var_id,
                    variant_type=var_type,
                    variant_subtype=var_sub_type,
                    phenotypes=parse_drug_resistance_info(hit.get("annotation", [])),
                    # location
                    reference_sequence=hit["gene_name"],
                    accession=hit["feature_id"],
                    start=int(hit["pos"]),
                    end=int(hit["pos"]) + len(alt_nt),
                    ref_nt=ref_nt,
                    alt_nt=alt_nt,
                    # consequense
                    variant_effect=hit["type"],
                    hgvs_nt_change=hit["nucleotide_change"],
                    hgvs_aa_change=hit["protein_change"],
                    # prediction info
                    depth=hit["depth"],
                    frequency=float(hit["freq"]),
                    method=variant_caller,
                    passed_qc=passed_qc,
                )
            )
            var_id += 1  # increment variant id
    # sort variants
    return sorted(results, key=lambda v: (v.reference_sequence, v.start))


def parse_drug_resistance_info(drugs: list[dict[str, str]]) -> list[PhenotypeInfo]:
    """Parse drug info into the standard format.

    :param drugs: TbProfiler drug info
    :type drugs: list[dict[str, str]]
    :return: Formatted phenotype info
    :rtype: list[PhenotypeInfo]
    """
    phenotypes: list[PhenotypeInfo] = []
    for drug in drugs:
        reference = drug.get("comment")
        phenotypes.append(
            PhenotypeInfo(
                name=drug["drug"],
                type=ElementType.AMR,
                reference=[] if reference is None else [reference],
                annotation_type=AnnotationType.TOOL,
                annotation_author=Software.TBPROFILER.value,
                note=drug.get("confidence"),
                source=drug.get("source"),
            )
        )
    return phenotypes


def _to_lineage_result(pred: dict[str, Any]) -> list[LineageInformation]:
    """Transpose prediction result into a lineage object."""

    return [
        LineageInformation(
            lineage=lin["lineage"],
            family=lin["family"],
            rd=lin["rd"],
            fraction=lin["fraction"],
            support=lin["support"],
        )
        for lin in (pred.get("lineage") or [])
    ]


class TbProfilerParser(BaseParser):
    """TbProfiler parser."""

    software = AnalysisSoftware.TBPROFILER
    parser_name = "TbProfilerParser"
    parser_version = 1
    schema_version = 1

    produces = {AnalysisType.AMR, AnalysisType.LINEAGE}

    def _parse_impl(
        self, source: ParserInput, *, want: set[AnalysisType], **kwargs: Any
    ) -> ParseImplOut:
        """Perform the bulk parsing."""

        data = read_json(source)

        out: dict[AnalysisType, Any] = {}

        if AnalysisType.AMR in want:
            self.log_info("Parsing AMR results")
            out[AnalysisType.AMR] = ElementTypeResult(
                phenotypes=_get_sr_profie(data),
                genes=[],
                variants=_parse_variants(data),
            )

        if AnalysisType.LINEAGE in want:
            self.log_info("Parsing AMR results")
            out[AnalysisType.LINEAGE] = _to_lineage_result(data)

        return out

    def get_version(self, source: ParserInput) -> SoupVersion | None:
        """
        Optional helper: extract db version info (if present).
        Not part of BaseParser, but consistent with your pattern elsewhere.
        """
        pred = read_json(source)
        db = pred.get("pipeline", {}).get("db_version")

        if not db:
            self.log_warning("TbProfiler output missing pipeline.db_version")
            return None

        return SoupVersion(
            name=db.get("name"),
            version=get_db_version(db),
            type=SoupType.DB,
        )
