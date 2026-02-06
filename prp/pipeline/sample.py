"""Parse for input config using parsers from this module."""

import logging
from pathlib import Path
from typing import Any

from prp.models.metadata import PipelineRun, PipelineInfo, SequencingInfo
from prp.models.manifest import SampleManifest
from prp.parse import run_parser
from prp.io.json import read_json

LOG = logging.getLogger(__name__)

def parse_jasen_run_info(source: Path) -> PipelineRun:
    """Parse the run information dump from JASEN."""

    raw_data = read_json(source)

    return PipelineRun(
        pipeline_run_id=raw_data.get('workflow_name'),
        executed_at=raw_data.get('date'),
        assay=raw_data.get('assay'),
        pipeline_info=PipelineInfo(
            pipeline_name='jasen',
            pipeline_version=raw_data.get('version') or raw_data.get('commit'),
        )
    )


def parse_results_from_manifest(manifest: SampleManifest) -> dict[str, Any]:
    """Parse pipeline analysis results from a manifest file."""

    result = {}

    # read how the pipeline was executed
    result["pipeline_run"] = parse_jasen_run_info(manifest.nextflow_run_info)

    return result