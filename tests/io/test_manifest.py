"""Testing functions reading manifest files."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from prp.io.manifest import read_bootstrap_config

def test_read_bootstrap_config_valid(bootstap_config_valid):
    """Test reading config file."""

    config = read_bootstrap_config(bootstap_config_valid)

    assert len(config.users) == 1
    assert len(config.groups) == 1


def test_read_bootstrap_config_missing_file(tmp_path):
    missing = tmp_path / "nope.yaml"
    with pytest.raises(FileNotFoundError):
        read_bootstrap_config(missing)


def test_read_bootstrap_config_invalid_shape(tmp_path):
    cfg = tmp_path / "bootstrap.yaml"
    cfg.write_text(
        """
        users:
          - username: user
            email: user@mail.com
            # password missing
            role: [user]
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        read_bootstrap_config(cfg)
