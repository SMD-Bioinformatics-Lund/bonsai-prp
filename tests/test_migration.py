"""Test migration of samples."""

from prp.migration import migrate_result


def test_migrate_result(saureus_v1_result, saureus_v2_result):
    """Test 'migrate_result' function."""