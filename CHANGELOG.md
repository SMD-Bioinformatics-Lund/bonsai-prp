## [Unreleased]

### Added

- Added `assay` and `release_life_cycle` to `PipelineInfo`
- Added `config.py` for migration
- Added parser for `gambitcore`
- Added tests and test files for `gambitcore`
- Added `sccmec` parsing, models and tests

### Fixed

- Fixed `workflow_name` no longer calls incorrect key (`commitId`)
- Changed `PipelineResult.model_validate_json` to `PipelineResult.model_validate` to fix validate bug
- Fixed sourmash signature upload bug
- Fixed erroneus empty array for resfinder
- Fixed mlst not being produced in json output

### Changed

- Changed parsing of metadata whereby `analysis_profile` doesn't need list comprehension
- Updated pytests regarding addition of `assay` and `release_life_cycle`

## [1.1.0]

### Added

- Added `spatyper` parsing, models and tests

### Fixed

- Fixed `spatyper` parser if no prediction

### Changed

- Changed processing of `sourmash` in config model

## [1.0.1]

### Added

### Fixed

- Fixed `publish_docker_on_commit_to_master.yml` & `publish_docker_on_release.yml`
- Fixed prp expecting `kraken` to always be in config (JASEN CI doesn't call `kraken`)

### Changed

## [1.0.0]

### Added

- Added command to upload samples to Bonsai.
- Added command for migrating old results to the new schema.

### Fixed

### Changed

- Analysis profiles are now stored as a list to handle multiple profiles.
- Replaced `create-bonsai-input` command with `parse`

## [0.11.5]

### Added

### Fixed

 - Fixed `bonsai-prp rerun-bonsai-input`
 - Fixed `.rstrip()` erroneous removal of "nln" suffix from end of sample id string (as it interprets it as a new line).
 - Fixed search for postalignqc files as suffix has changed from `_bwa.qc` to `_qc.json`.
 - Removed the inclusion Serotypefinder for saureus samples.
 - AmrFinder parser now correctly reports variants.

### Changed

## [0.11.4]

### Added

### Fixed

 - Fixed NG50 bug that couldn't process "-"

### Changed

## [0.11.3]

### Added

 - Added NG50 to bonsai input

### Fixed

### Changed

## [0.11.2]

### Added

### Fixed

 - Fixed issue where mlst results with no calls crashed PRP.

### Changed

 - Added mypy as test dependency

## [0.11.1]

### Added

### Fixed

 - Handle alt types for emmtyper

### Changed

## [0.11.0]

### Added

 - Added emmtyper and parser
 - Added pytests for emmtyper

### Fixed

### Changed

 - Changed Shigapass models to be consistent with other typing models
 - Changed Shigapass parsers to be consistent with other typing parsers
 - Changed ref genome related variables to be optional in quast

## [0.10.1]

### Added

### Fixed

 - Updated parsing of ChewBBACA allele calling annotations and novel alleles. This adds support for annotations introduced in v3.

### Changed

## [0.10.0]

### Added

 - Added flag to set verbosity level.
 - Validate TbProfiler schema version.
 - Added CLI command for adding IGV annotation tracks
 - Added `indel_variants` to json result and ability to filter vcf into various categories

### Fixed

 - Fixed genome_annotation appending bug
 - Fixed variant sorting as `reference_sequence` can be None

### Changed

 - Updated sample metadata in the output format. RunMetadata was split into two fields, one for sequencing and one for pipeline information. Lims id and sample name are now included in the SampleBase object.
 - Split SV and SNV from tbprofiler output
 - Update annotate_delly to extract SVs from vcf

## [0.9.3]

### Added

 - Add `sample_id` to prp output

### Fixed

### Changed

## [0.9.2]

### Added

### Fixed

 - Changed `--symlink_dir` to `--symlink-dir` for consistency

### Changed

 - Use `basename` when `symlink_dir` provided

## [0.9.1]

### Added

 - Added additional tests to ensure that Bonsai input data can be re-cast into a `PipelineResult` data format.

### Fixed

### Changed

 - Fixed some Pylint warnings.
 - Pylint ignores pysam functions since they are generated.

## [0.9.0]

### Added

 - Added Shigapass output
 - Added tests for the Shigapass parser.

### Fixed

 - Fixed minor issues with the ShigaPass parser.

### Changed

## [0.8.3]

### Added

### Fixed

 - Reordered lineage data models in the method index.

### Changed

## [0.8.2]

### Added

### Fixed

 - Updated lineage parser to work with TbProfiler v6.2

### Changed

 - Changes lineage datamodel to reflect changes in TbProfiler output

## [0.8.1]

### Added

 - Added species prediction and phylo group from Mykrobe.

### Fixed

### Changed

 - Changed `species_prediction` field to be a key-value indexed array to support multiple SPP predictions.

## [0.8.0]

### Added

 - Added `rerun_bonsai_input` to rerun bonsai-prp outputs when output format changes
 - Added `symlink_dir` as possible filepaths prefix for IGV inputs
 - Added kraken cutoff whereby species prediction needs to have >= 0.01% of read hits
 - Added phylogenetic statistics to result for tb
 - Added source of variant to output

### Fixed

 - Handling of tbprofiler v6.2.0 results

### Changed

 - Changed all click types to click.Path()
 - Removed `ref_accession != bam_ref_genome` check

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
