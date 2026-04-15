"""Test manifest models."""

import pytest
from pathlib import Path
from pydantic import BaseModel, ValidationError
from prp.models.manifest import FlexibleURI, URI

class Model(BaseModel):
    """Test model."""

    uri: FlexibleURI


def test_s3_uri():
    """Test parsing of s3 URI string."""

    m = Model(uri="s3://bucket/path/to/file")
    assert m.uri.scheme == "s3"
    assert m.uri.netloc == "bucket"
    assert m.uri.path == "/path/to/file"
    assert str(m.uri) == "s3:///path/to/file" # Enligt din __str__ implementation


def test_local_path_exists(tmp_path):
    """Test that a local path is resolved."""

    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    
    m = Model(uri=str(test_file))
    assert m.uri.scheme == "file"
    assert m.uri.path == test_file.as_posix()


def test_relative_path_with_context(tmp_path):
    """Test that a relative path."""

    # Create a csv file in project folder
    # /project/data.csv
    base_dir = tmp_path / "project"
    base_dir.mkdir()
    data_file = base_dir / "data.csv"
    data_file.touch()
    
    # Simulate a manifest file in project folder
    config_file = base_dir / "config.yaml"
    
    # Use relative path and pass context input model
    m = Model.model_validate(
        {"uri": "data.csv"},
        context=config_file
    )
    
    assert m.uri.scheme == "file"
    assert m.uri.path == data_file.as_posix()


def test_invalid_input():
    """Assert that invalid data causes error."""

    with pytest.raises(ValidationError):
        Model(uri="inte-en-fil-och-inget-schema")

def test_non_existent_file_raises_error():
    """Test that passing a non-existant file raises an error."""

    invalid_path = "this_file_does_not_exist.txt"
    
    with pytest.raises(ValidationError) as exc_info:
        Model(uri=invalid_path)
    
    assert "Invalid URI or path" in str(exc_info.value)


def test_missing_relative_path_with_context(tmp_path):
    """Test that missing file raises an error if context exists."""

    config_file = tmp_path / "config.yaml"
    
    with pytest.raises(ValidationError):
        Model.model_validate(
            {"uri": "missing_data.csv"}, 
            context=config_file
        )


def test_path_object_input(tmp_path):
    """Test using file:// scheme as input."""

    test_path = tmp_path / "file.json"
    test_path.touch()
    
    m = Model(uri=test_path)
    assert m.uri.scheme == "file"
    assert isinstance(m.uri, URI)