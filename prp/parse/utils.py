"""Shared utility functions."""
import os
from datetime import datetime

from ..models.phenotype import (
    ElementType,
    ElementTypeResult,
    PhenotypeInfo,
    VariantSubType,
)


def _default_amr_phenotype() -> PhenotypeInfo:
    return PhenotypeInfo(
        type=ElementType.AMR,
        group=ElementType.AMR,
        name=ElementType.AMR,
    )


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


def _get_path(symlink_dir: str, subdir: str, filepath: str) -> str:
    """Get absolute/symlink path"""
    return (
        os.path.join(symlink_dir, subdir, os.path.basename(filepath))
        if symlink_dir
        else os.path.realpath(filepath)
    )


def parse_input_dir(
    input_dir: str, jasen_dir: str, symlink_dir: str, output_dir: str
) -> list[dict[str, str]]:
    """Create a sample input array per sample in directory.

    :param input_dir: Input directory path
    :type input_dir: str
    :param jasen_dir: JASEN install directory path
    :type jasen_dir: str
    :param symlink_dir: Nextflow publish directory path
    :type symlink_dir: str
    :param output_dir: Output directory path
    :type output_dir: str
    :return: A list of sample arrays
    :rtype: list[dict[str, str]]
    """
    input_arrays = []
    input_dir = input_dir.rstrip("/")
    species = input_dir.split("/")[-1]
    output_dir = (
        os.path.join(input_dir, "analysis_result") if not output_dir else output_dir
    )
    if os.path.exists(input_dir):
        analysis_results_dir = os.path.join(input_dir, "analysis_result")
        for filename in os.listdir(analysis_results_dir):
            if filename.endswith(".json"):
                sample_id = filename.rstrip("_result.json")
                sample_array = create_sample_array(
                    species, input_dir, jasen_dir, sample_id, symlink_dir, output_dir
                )
                input_arrays.append(sample_array)
    return input_arrays


def create_sample_array(
    species: str,
    input_dir: str,
    jasen_dir: str,
    sample_id: str,
    symlink_dir: str,
    output_dir: str,
) -> dict[str, str]:
    """Create an index wiht all sample files.

    :param species: species name
    :type species: str
    :param input_dir: Input directory path
    :type input_dir: str
    :param jasen_dir: JASEN install directory path
    :type jasen_dir: str
    :param sample_id: Sample id
    :type sample_id: str
    :param symlink_dir: Nextflow publish directory
    :type symlink_dir: str
    :param output_dir: Output directory
    :type output_dir: str
    :return: Collection of files used as input
    :rtype: dict[str, str]
    """
    output = os.path.abspath(os.path.join(output_dir, f"{sample_id}_result.json"))
    bam = os.path.abspath(os.path.join(input_dir, f"bam/{sample_id}.bam"))
    kraken = os.path.abspath(os.path.join(input_dir, f"kraken/{sample_id}_bracken.out"))
    quality = os.path.abspath(
        os.path.join(input_dir, f"postalignqc/{sample_id}_bwa.qc")
    )
    quast = os.path.abspath(os.path.join(input_dir, f"quast/{sample_id}_quast.tsv"))
    run_metadata = os.path.abspath(
        os.path.join(input_dir, f"analysis_metadata/{sample_id}_analysis_meta.json")
    )
    if species == "mtuberculosis":
        reference_genome_fasta = os.path.abspath(
            os.path.join(
                jasen_dir,
                "assets/genomes/mycobacterium_tuberculosis/GCF_000195955.2.fasta",
            )
        )
        reference_genome_gff = os.path.abspath(
            os.path.join(
                jasen_dir,
                "assets/genomes/mycobacterium_tuberculosis/GCF_000195955.2.gff",
            )
        )
        sv_vcf = os.path.abspath(
            os.path.join(input_dir, f"annotate_delly/{sample_id}_annotated_delly.vcf")
        )
        mykrobe = os.path.abspath(
            os.path.join(input_dir, f"mykrobe/{sample_id}_mykrobe.csv")
        )
        tbprofiler = os.path.abspath(
            os.path.join(input_dir, f"tbprofiler_mergedb/{sample_id}_tbprofiler.json")
        )
        return {
            "output": output,
            "bam": bam,
            "genome_annotation": [],
            "kraken": kraken,
            "quality": quality,
            "quast": quast,
            "reference_genome_fasta": reference_genome_fasta,
            "reference_genome_gff": reference_genome_gff,
            "run_metadata": run_metadata,
            "sample_id": sample_id,
            "snv_vcf": None,
            "sv_vcf": sv_vcf,
            "mykrobe": mykrobe,
            "tbprofiler": tbprofiler,
            "symlink_dir": symlink_dir,
            "amrfinder": None,
            "cgmlst": None,
            "mlst": None,
            "resfinder": None,
            "serotypefinder": None,
            "virulencefinder": None,
            "process_metadata": [],
        }
    if species in ("saureus", "ecoli", "kpneumoniae"):
        process_metadata = []
        amrfinder = os.path.abspath(
            os.path.join(input_dir, f"amrfinderplus/{sample_id}_amrfinder.out")
        )
        cgmlst = os.path.abspath(
            os.path.join(input_dir, f"chewbbaca/{sample_id}_chewbbaca.out")
        )
        mlst = os.path.abspath(os.path.join(input_dir, f"mlst/{sample_id}_mlst.json"))
        resfinder = os.path.abspath(
            os.path.join(input_dir, f"resfinder/{sample_id}_resfinder.json")
        )
        resfinder_meta = os.path.abspath(
            os.path.join(input_dir, f"resfinder/{sample_id}_resfinder_meta.json")
        )
        serotypefinder = os.path.abspath(
            os.path.join(input_dir, f"serotypefinder/{sample_id}_serotypefinder.json")
        )
        serotypefinder_meta = os.path.abspath(
            os.path.join(
                input_dir, f"serotypefinder/{sample_id}_serotypefinder_meta.json"
            )
        )
        virulencefinder = os.path.abspath(
            os.path.join(input_dir, f"virulencefinder/{sample_id}_virulencefinder.json")
        )
        virulencefinder_meta = os.path.abspath(
            os.path.join(
                input_dir, f"virulencefinder/{sample_id}_virulencefinder_meta.json"
            )
        )
        process_metadata.append(resfinder_meta)
        process_metadata.append(serotypefinder_meta)
        process_metadata.append(virulencefinder_meta)
        if species == "saureus":
            reference_genome_fasta = os.path.abspath(
                os.path.join(
                    jasen_dir,
                    "assets/genomes/staphylococcus_aureus/GCF_000012045.1.fasta",
                )
            )
            reference_genome_gff = os.path.abspath(
                os.path.join(
                    jasen_dir,
                    "assets/genomes/staphylococcus_aureus/GCF_000012045.1.gff",
                )
            )
        if species == "ecoli":
            reference_genome_fasta = os.path.abspath(
                os.path.join(
                    jasen_dir, "assets/genomes/escherichia_coli/GCF_000005845.2.fasta"
                )
            )
            reference_genome_gff = os.path.abspath(
                os.path.join(
                    jasen_dir, "assets/genomes/escherichia_coli/GCF_000005845.2.gff"
                )
            )
        if species == "kpneumoniae":
            reference_genome_fasta = os.path.abspath(
                os.path.join(
                    jasen_dir,
                    "assets/genomes/klebsiella_pneumoniae/GCF_000240185.1.fasta",
                )
            )
            reference_genome_gff = os.path.abspath(
                os.path.join(
                    jasen_dir,
                    "assets/genomes/klebsiella_pneumoniae/GCF_000240185.1.gff",
                )
            )
        return {
            "output": output,
            "bam": bam,
            "genome_annotation": [],
            "kraken": kraken,
            "quality": quality,
            "quast": quast,
            "reference_genome_fasta": reference_genome_fasta,
            "reference_genome_gff": reference_genome_gff,
            "run_metadata": run_metadata,
            "sample_id": sample_id,
            "snv_vcf": None,
            "sv_vcf": None,
            "mykrobe": None,
            "tbprofiler": None,
            "symlink_dir": symlink_dir,
            "amrfinder": amrfinder,
            "cgmlst": cgmlst,
            "mlst": mlst,
            "resfinder": resfinder,
            "serotypefinder": serotypefinder,
            "virulencefinder": virulencefinder,
            "process_metadata": process_metadata,
        }
    return None
