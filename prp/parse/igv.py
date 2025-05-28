"""Parse metadata passed to pipeline."""

import logging
from pathlib import Path

from prp.models.config import IgvAnnotation

from ..models.sample import IgvAnnotationTrack, ReferenceGenome

LOG = logging.getLogger(__name__)


def parse_igv_info(
    ref_genome_sequence: Path,
    ref_genome_annotation: Path,
    igv_annotations: list[IgvAnnotation],
) -> tuple[ReferenceGenome, str | None, list[IgvAnnotationTrack]]:
    """Parse IGV information.

    :param reference_genome: Nextflow analysis metadata in json format.
    :type reference_genome: str
    :return: Reference genome information.
    :rtype: ReferenceGenome
    """
    LOG.info("Parse IGV info.")

    read_mapping_info: list[IgvAnnotationTrack] = []

    igv_alignment_track: str | None = None
    for annotation in igv_annotations:
        if annotation.type == "alignment":
            igv_alignment_track = annotation.uri
        else:
            igv_annotation_track = IgvAnnotationTrack(
                name=annotation.name,
                file=annotation.uri,
            )
            read_mapping_info.append(igv_annotation_track)

    ref_genome_sequence_fai = ref_genome_sequence.parent / (
        ref_genome_sequence.name + ".fai"
    )
    species_name = ref_genome_sequence.parent.name.replace("_", " ")

    reference_genome_info = ReferenceGenome(
        name=species_name.capitalize(),
        accession=str(ref_genome_sequence.stem),
        fasta=str(ref_genome_sequence),
        fasta_index=str(ref_genome_sequence_fai),
        genes=str(ref_genome_annotation),
    )

    return reference_genome_info, igv_alignment_track, read_mapping_info
