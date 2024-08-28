# Pipeline result processor (prp)
*A collection of parsers and data models for creation and validation of a standardized output for the [jasen](https://github.com/genomic-medicine-sweden/jasen) pipeline which is used as an input for [bonsai](https://github.com/Clinical-Genomics-Lund/bonsai).*

> [!WARNING]
> Bonsai-PRP is under development in an alpha stage. Expect uneven documentation, breaking changes, and bugs until the official 1.0 release.

## Dependencies (latest)
* biopython
* pydantic=2.5.3
* python=3.10

## Using prp
### Use the help argument for information regarding the prp's methods
```
prp --help
```

### Use the method help argument for information regarding the input for each of prp's methods (`add-igv-annotation-track`, `annotate-delly`, `create-bonsai-input`, `create-cdm-input`, `create-qc-result`, `print-schema`, `rerun-bonsai-input`, `validate`)
```
prp <method> --help
```

### Create bonsai input from pipeline data
```
prp create-bonsai-input -i SAMPLE_ID -u RUN_METADATA_FILE -q QUAST_FILENAME -d PROCESS_METADATA_FILE -k KRAKEN_FILE -a AMRFINDER_FILE -m MLST_FILE -c CGMLST_FILE -v VIRULENCEFINDER_FILE -r RESFINDER_FILE -p POSTALIGNQC_FILE -k MYKROBE_FILE -t TBPROFILER_FILE --vcf VCF_FILE [--snv-vcf SNV_VCF_FILE] [--sv-vcf SV_VCF_FILE] [--symlink-dir SYMLINK_DIR] [--correct_alleles] -o OUTPUT_FILE [-h]
```

### Create CDM input from pipeline data
```
prp create-cdm-input -q QUAST_FILENAME -c CGMLST_FILE -p POSTALIGNQC_FILE [--correct_alleles] -o OUTPUT_FILE [-h]
```

### Create QC result from bam file
```
prp create-qc-result -i SAMPLE_ID --b BAM_FILE [-e BED_FILE] [-a BAITS_FILE] -r REFERENCE_FILE [-c CPUS] -o OUTPUT_FILE [-h]
```

### Rerun bonsai input creation for all samples
```
prp rerun-bonsai-input -i INPUT_DIR  -j JASEN_DIR -s SYMLINK_DIR -o OUTPUT_DIR -o OUTPUT_FILE [-h]
```

### Add IGV annotation track to result
```
prp add-igv-annotation-track -n TRACK_NAME -a ANNOTATION_FILE -b BONSAI_INPUT_FILE -o OUTPUT_FILE [-h]
```

### Validate output format of result json file
```
prp validate -o OUTPUT_FILE [-h]
```
