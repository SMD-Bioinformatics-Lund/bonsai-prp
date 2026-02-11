
import logging

import click

from prp.models.base import OptionalFile

LOG = logging.getLogger(__name__)


@click.group("analysis")
def analysis_gr():
    """Commands for conducting analysis"""
    ...

@analysis_gr.command("alignment_qc")
@click.option("-i", "--sample-id", required=True, help="Sample identifier")
@click.option("-b", "--bam", required=True, type=click.File(), help="bam file")
@click.option("-e", "--bed", type=click.File(), help="bed file")
@click.option("-a", "--baits", type=click.File(), help="baits file")
@click.option(
    "-r", "--reference", required=True, type=click.File(), help="reference fasta"
)
@click.option("-c", "--cpus", type=click.INT, default=1, help="cpus")
@click.option(
    "-o", "--output", required=True, type=click.File("w"), help="output filepath"
)
def create_qc_result(
    sample_id: str,
    bam: click.File,
    bed: OptionalFile,
    baits: OptionalFile,
    reference: OptionalFile,
    cpus: int,
    output: click.File,
) -> None:
    """Generate QC metrics regarding bam file"""
    try:
        from prp.analysis.qc import parse_alignment_results
    except RuntimeError as exc:
        click.secho(str(exc), fg="red")

    # the logic
    if bam and reference:
        LOG.info("Parse alignment results")
        parse_alignment_results(sample_id, bam, reference, cpus, output, bed, baits)
    click.secho("Finished generating QC output", fg="green")