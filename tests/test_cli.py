"""Test PRP cli functions."""

from click.testing import CliRunner

from bonsai_libs.api_client.bonsai.models import (
    CreateUserInput,
    CreateGroupInput,
    CreateReferenceGenomeInput,
)

from prp.cli.bonsai_api import bonsai_bootstrap


def test_bootstrap_happy_path_calls_ensure_methods(monkeypatch, bootstap_config_valid):
    """Test that bootstrap cli calls the expected paths"""
    # --- Fake client ---
    class FakeClient:
        def authenticate_user(self, username, password):
            assert username == "admin"
            assert password == "secret"
            return True

    # --- Capture calls ---
    calls = {"users": [], "groups": [], "reference_genomes": []}

    class FakeService:
        def __init__(self, client, state_store, dry_run=False, **kwargs):
            self.client = client
            self.state_store = state_store
            self.dry_run = dry_run

        def ensure_user_exists(self, user_id, **user_data):
            calls["users"].append((user_id, user_data))
            return {"username": user_id}

        def ensure_group_exists(self, group_id, **group_data):
            calls["groups"].append((group_id, group_data))
            return {"id": group_id}

        def ensure_reference_genome_exists(self, reference_genome, **ref_data):
            calls["reference_genomes"].append((reference_genome, ref_data))
            return {"id": getattr(reference_genome, "accession", None)}

    # Monkeypatch wiring in CLI module

    # 1. make_bonsai_client() returns our fake client
    monkeypatch.setattr("prp.cli.bonsai_api.make_bonsai_client", lambda base_url: FakeClient())
    # 2. BonsaiUploadService is replaced with our fake service
    monkeypatch.setattr("prp.cli.bonsai_api.BonsaiUploadService", FakeService)

    runner = CliRunner()
    with runner.isolated_filesystem():
        # invoke: use default config_file path
        cfg_path = str(bootstap_config_valid.absolute())
        result = runner.invoke(
            bonsai_bootstrap,
            [cfg_path, "-a", "http://api:8000", "-u", "admin", "-p", "secret"],
        )

    assert result.exit_code == 0, result.output

    # --- Verify calls ---
    assert isinstance(calls["users"][0][0], CreateUserInput)
    assert isinstance(calls["groups"][0][0], CreateGroupInput)
    assert isinstance(calls["reference_genomes"][0][0], CreateReferenceGenomeInput)
