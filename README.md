# Pipeline result processor (prp): A collection of parsers and data models for creation and validation of a standardized output for the [jasen](https://github.com/genomic-medicine-sweden/jasen) pipeline which is used as an input for [bonsai](https://github.com/Clinical-Genomics-Lund/bonsai)

## Dependencies (latest)
* biopython
* pydantic=2.5.3
* python=3.10

## Using prp
### Use the help argument for information regarding the Jasentool's methods
```
prp --help
```

### Use the method help argument for information regarding the input for each of Jasentool's methods (`create-bonsai-input`, `create-cdm-input`, `print-schema`, `validate`)
```
prp <method> --help
```

### Create bonsai input from pipeline data
```
prp create-bonsai-input -i SAMPLE_ID -u RUN_METADATA_FILE [required] -q QUAST_FILENAME -d PROCESS_METADATA_FILE -k KRAKEN_FILE -a AMRFINDER_FILE -m MLST_FILE -c CGMLST_FILE -v VIRULENCEFINDER_FILE -r RESFINDER_FILE -p POSTALIGNQC_FILE -k MYKROBE_FILE -t TBPROFILER_FILE [--correct_alleles] -o OUTPUT_FILE [-h]
```

### Create CDM input from pipeline data
```
prp create-cdm-input -q QUAST_FILENAME -c CGMLST_FILE -p POSTALIGNQC_FILE [--correct_alleles] -o OUTPUT_FILE [-h]
```
