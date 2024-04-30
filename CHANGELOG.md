## [Unreleased]

### Added

 - Add `rerun_bonsai_input` to rerun bonsai-prp outputs when output format changes
 - Add `symlink_dir` as possible filepaths prefix for IGV inputs
 - Added kraken cutoff whereby species prediction needs to have >= 0.01% of read hits

### Fixed

### Changed

## [0.7.1]

### Added

### Fixed

 - Fixed `ins_size`, `ins_size_dev` & `coverage_uniformity` parsing and models
 - Check first 1000 reads if paired instead of just first read

### Changed

## [0.7.0]

### Added

 - Added `sequencing_run` and `lims_id` to output (bonsai input)
 - Added function for annotating delly variants intersecting with resistance targets
 - Added capability of handling empty dictionaries from serotypefinder output
 - Added pytest for `prp annotate-delly`
 - Added `pyyaml` to docker image

### Fixed

 - Fixed `--output` arg re annotate delly

### Changed

 - Removed sample id from Sample object
 - Changed annotate delly output type

## [0.6.0]

### Added

 - Add optional SNV and structural variants to sample output
 - Add `n_read_pairs`

### Fixed

 - Calculation of `iqr_median` (now called `coverage_uniformity`)

### Changed

 - Renamed variables to be more informative (`median` to `median_cov`, `tot_reads` to `n_reads` & `mapped_reads` to `n_mapped_reads`)

## [0.5.0]

### Added

 - Add models for serotypefinder results
 - Add fx to parse serotypefinder results
 - Add --serotypefinder arg to cli
 - Add files for pytest re serotypefinder results for ecoli

### Fixed

 - Handle amrfinder --organism output

### Changed

 - Update pytest functions to incl. serotypefinder results for ecoli

## [0.4.0]

### Added

 - Add create-qc-result as sub arguement
 - Add QC class and parse_alignment_results to qc.py
 - Add picard, sambamba, java and r-base to Dockerfile
 - Add quartile1, median & quartile3 to postalignqc results and respective model
 - Add fx for formatting datetime for manually generated tbdbs

### Fixed

 - Dockerfile python version
 - Pydantic models
 - Python version error in Dockerfile
 - Test files regarding q1, median and q3

### Changed

 - Workflow that publishes to PyPI and Dockerhub separated into two workflows for testing
 - Publish to docker workflow started on completion of PyPI publishing
 - Changed VariantTypes and added VariantSuptype classification

## [0.3.1]

### Added

 - Workflow for docker image to be pushed to dockerhub
 - Image build file (Dockerfile)
 - Add get_db_version and reformat_date_str to utils.py
 - Workflow that builds and pushes to both dockerhub and PyPI

### Fixed

 - Git action versions

### Changed

 - Move utils.py from prp/parse/phenotype to prp/parse
 - Docker/PyPI publishing workflow added workflow_dispatch, removed permissions and changed secret variable names

## [0.3.0]

### Added

 - Pytest for Mycobacterium tuberculosis

### Fixed

 - Reordered variant models in ElementTypeResult
 - Fixed assignment of TbProfiler variant type

### Changed

 - Renamed mutations to variants
 - Removed prc_dup and dup from postAlnQc output
 - Added reference, note fields to PhenotypeInfo
 - Mykrobe output parser handles csv format instead of json
 - Split generic ResistanceVariant and ResistanceGene to one specified for individual tools
 - Include non resistance yeilding variants from tbprofiler

## [0.2.0]

### Added

 - CLI command for generating QC report for CDM
 - Parsing of Virulencefinder STX typing

### Fixed

 - Bug that prevented parsing of AMRfinder results

### Changed

 - Resfinder variant describe changed NT instead of codon.
 - Antibiotic class is stored with phenotypes.
 - Accession nr, gene symbol and AA change is stored for Resfinder variants

## [0.1.0]

### Added

 - Added PRP application from https://github.com/genomic-medicine-sweden/JASEN
 - CHANGELOG reminder github action for PRs
 - Test and test files for S.aureus and E.coli
 - Pytest github action

### Fixed

### Changed
