## [Unreleased]

### Added

 - Add models for serotypefinder results
 - Add fx to parse serotypefinder results
 - Add --serotypefinder arg to cli

### Fixed

### Changed

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
