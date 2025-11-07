"""Fixtures"""

from .ecoli import *
from .kpneumoniae import *
from .mtuberculosis import *
from .saureus import *
from .shigella import *
from .streptococcus import *


@pytest.fixture()
def mlst_result_path_no_call(data_path: Path) -> Path:
    """Get path for mlst file where alleles was not called."""
    return data_path.joinpath("mlst.nocall.json")
