"""Test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture()
def bootstap_config_valid(tmp_path: Path) -> Path:
    """Create a valid bootstrap config."""
    cfg = tmp_path / "default.yaml"
    cfg.write_text(
        """
        users:
          - username: user
            email: user@mail.com
            password: user123
            role: [user]
        groups:
          - group_id: mtuberculosis
            display_name: "M. tuberculosis"
            description: "Tuberculosis test samples"
        reference_genomes:
          - name: mtuberculosis
            accession: TEST123
            organism: Mycobacterium tubcerculosis
            fasta_resource: genome.fasta
            fasta_index_resource: genome.fasta.fai
            reference_tracks:
              - name: Rifampicin resistance-determining region
                format: bed
                type: annotation
                path: annotation.bed
    """, encoding="utf-8")
    return cfg
