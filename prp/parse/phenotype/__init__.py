"""Module for parsing resistance prediction results."""

from .amrfinder import parse_amrfinder_amr_pred, parse_amrfinder_vir_pred
from .mykrobe import parse_mykrobe_amr_pred
from .resfinder import parse_resfinder_amr_pred
from .shigapass import parse_shigapass_pred
from .tbprofiler import parse_tbprofiler_amr_pred
from .virulencefinder import parse_virulencefinder_vir_pred
