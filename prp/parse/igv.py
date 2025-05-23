"""Parse metadata passed to pipeline."""

import os
import logging
from pathlib import Path

from ..models.sample import (
    ReferenceGenome,
    IgvAnnotationTrack,
)

LOG = logging.getLogger(__name__)


def parse_igv_info(
    ref_genome_sequence: Path, ref_genome_annotation: Path, igv_annotations: list[str]
) -> tuple[ReferenceGenome, str, list[dict]]:
    """Parse IGV information.

    :param reference_genome: Nextflow analysis metadata in json format.
    :type reference_genome: str
    :return: Reference genome information.
    :rtype: ReferenceGenome
    """
    LOG.info("Parse IGV info.")

    read_mapping_info = []

    for annotation in igv_annotations:
        if annotation.type == "alignment":
            igv_alignment_track = annotation.uri
        else:
            igv_annotation_track = IgvAnnotationTrack(
                name=annotation.name,
                file=annotation.uri,
            )
            read_mapping_info.append(igv_annotation_track)

    ref_genome_sequence_fai = Path(str(ref_genome_sequence) + ".fai")
    species_name = str(ref_genome_sequence).split("/")[-2].replace("_", " ")

    reference_genome_info = ReferenceGenome(
        name=species_name[0].upper() + species_name[1:],
        accession=str(ref_genome_sequence.stem),
        fasta=str(ref_genome_sequence),
        fasta_index=str(ref_genome_sequence_fai),
        genes=str(ref_genome_annotation),
    )

    return reference_genome_info, igv_alignment_track, read_mapping_info
