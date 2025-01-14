"""Fixtures"""

from .ecoli import *
from .mtuberculosis import *
from .saureus import *
from .shigella import *
from .streptococcus import *


@pytest.fixture()
def mlst_result_path_no_call(data_path):
    """Get path for mlst file where alleles was not called."""
    return str(data_path.joinpath("mlst.nocall.json"))
