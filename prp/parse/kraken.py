"""Parse kraken results."""

from typing import Any

from prp.exceptions import ParserError
from prp.models.base import AnalysisType, ParserOutput
from prp.models.species import BrackenSpeciesPrediction, BrackenSppIndex, TaxLevel

from .base import BaseParser, ParserInput
from .registry import register_parser
from .utils import read_delimited, safe_float, safe_int

BRACKEN = "bracken"
REQUIRED_COLUMNS = {
    "name",
    "taxonomy_id",
    "taxonomy_lvl",
    "kraken_assigned_reads",
    "added_reads",
    "new_est_reads",
    "fraction_total_reads",
}


def _validate_columns(row: dict[str, object], *, strict: bool = False) -> None:
    cols = set(row.keys())
    missing = REQUIRED_COLUMNS - cols
    if missing:
        raise ValueError(f"Bracken file missing columns: {sorted(missing)}; got: {sorted(cols)}")

    if strict:
        extra = cols - REQUIRED_COLUMNS
        if extra:
            raise ValueError(f"Bracken file has unexpected extra columns: {sorted(extra)}")


def to_taxlevel(lvl: str | TaxLevel) -> TaxLevel:
    if isinstance(lvl, TaxLevel):
        return lvl

    lvl = lvl.strip()
    if not lvl:
        raise ValueError("Empty taxonomic level")

    # 1) Try as enum NAME (e.g. "S", "G")
    try:
        return TaxLevel[lvl.upper()]
    except KeyError:
        pass

    # 2) Try as enum VALUE (e.g. "species", "genus")
    try:
        return TaxLevel(lvl.lower())
    except ValueError as exc:
        raise ValueError(f"Unknown taxonomic level: {lvl!r}") from exc


@register_parser(BRACKEN)
class BrackenParser(BaseParser):

    software = BRACKEN
    parser_name = "BrackenParser"
    parser_version = "1"
    schema_version = 1
    produces = {AnalysisType.SPECIES}

    def parse(self, 
              data: ParserInput, 
              *, 
              want: set[AnalysisType] | None = None, 
              cutoff: float | None = None,
              strict_columns: bool = False
              ) -> ParserOutput:
        """Parse Bracken results."""

        want = want or self.produces

        out = ParserOutput(
            software=self.software,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            results={},
        )

        if AnalysisType.SPECIES not in want:
            self.log_info(f"Skipping Bracken parse; requested analyses={want}")
            return out

        rows = read_delimited(data)
        try:
            first_row = next(rows)
            self.log_info("Bracken input is empty")
        except StopIteration:
            # empty file
            out.results[AnalysisType.SPECIES.value] = []
            return out
        
        # Validate the columns in the first row
        _validate_columns(first_row, strict=strict_columns)
        
        results: list[BrackenSpeciesPrediction] = []
        # append first row
        if (spp_obj := self._to_spp_results(first_row, cutoff=cutoff)):
            results.append(spp_obj)

        for row in rows:
            spp_obj = self._to_spp_results(row, cutoff=cutoff)
            if spp_obj is not None:
                results.append(spp_obj)
        
        if results:
            out.results[AnalysisType.SPECIES.value] = results
        return out
    
    def _to_spp_results(self, row: dict[str, Any], *, cutoff: float | None = None) -> BrackenSpeciesPrediction | None:
        """Convert row to Species prediction result"""

        try:
            raw_frac = row['fraction_total_reads']
            frac = float(raw_frac)
        except (TypeError, ValueError) as exc:
            raise ParserError(f"Invalid fraction_total_reads, fraction_total_reads={raw_frac}") from exc

        if cutoff is not None and frac < cutoff:
            return
        
        tax_level = to_taxlevel(row["taxonomy_lvl"])
        return BrackenSpeciesPrediction(
            scientific_name=row['name'],
            taxonomy_id=row['taxonomy_id'],
            taxonomy_lvl=tax_level,
            kraken_assigned_reads=safe_int(row['kraken_assigned_reads'], logger=self.logger),
            added_reads=safe_int(row['added_reads'], logger=self.logger),
            fraction_total_reads=safe_float(row['fraction_total_reads'], logger=self.logger)
        )
