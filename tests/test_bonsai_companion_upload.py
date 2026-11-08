"""Companion-file routing through the uploader, without parsing biology data."""
from types import SimpleNamespace

import pytest

from prp.bonsai.service import BonsaiUploadService, UploadStateStore
from prp.models.manifest import URI
from prp.pipeline.types import MinimalAnalysisRecord


def run_upload(tmp_path, definitions, only):
    records = []
    paths = {}
    for software, subcommand in definitions:
        path = tmp_path / (software + (subcommand or '') + '.txt')
        path.write_text('generic transport fixture\n')
        paths[(software, subcommand)] = path
        records.append(MinimalAnalysisRecord(software=software, subcommand=subcommand,
            software_version='1.0.0', uri=URI(scheme='file', path=str(path))))
    calls = []
    class Client:
        def upload_analysis_result(self, payload, **kwargs):
            calls.append(payload)
            return SimpleNamespace(analysis_id='analysis-1', software=payload.software,
                software_version=payload.software_version, envelopes={})
    result = SimpleNamespace(sample_id='existing-sample', pipeline=SimpleNamespace(pipeline_run_id='run-1'), analysis_results=records)
    service = BonsaiUploadService(client=Client(), state_store=UploadStateStore(root=tmp_path / 'state'), workflow_id='fixture')
    service.upload_sample(result, force=False, only=only)
    return calls, paths


@pytest.mark.parametrize('companion_first', [False, True])
def test_companion_attached_and_not_uploaded_separately(tmp_path, companion_first):
    definitions = [('kleborate', None), ('hAMRonization', None)]
    if companion_first:
        definitions.reverse()
    calls, paths = run_upload(tmp_path, definitions, {'kleborate', 'hAMRonization'})
    assert len(calls) == 1
    assert calls[0].software == 'kleborate'
    assert calls[0].hamronization_file == paths[('hAMRonization', None)]


def test_selected_primary_still_receives_companion(tmp_path):
    calls, paths = run_upload(tmp_path, [('kleborate', None), ('hAMRonization', None)], {'kleborate'})
    assert len(calls) == 1
    assert calls[0].hamronization_file == paths[('hAMRonization', None)]


def test_missing_companion_is_left_unset(tmp_path):
    calls, _ = run_upload(tmp_path, [('kleborate', None)], {'kleborate'})
    assert len(calls) == 1
    assert calls[0].hamronization_file is None


def test_samtools_auxiliary_binding_is_preserved(tmp_path):
    calls, paths = run_upload(tmp_path, [('samtools', 'stats'), ('samtools', 'bedcov')], {'samtools'})
    assert len(calls) == 1
    assert calls[0].bedcov_file == paths[('samtools', 'bedcov')]
    assert calls[0].hamronization_file is None
