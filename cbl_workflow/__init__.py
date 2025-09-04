import sys
import warnings

import building_data_utilities
import building_data_utilities.utils

warnings.warn(
    "The 'cbl_workflow' package is deprecated. Please use 'building_data_utilities' instead.",
    DeprecationWarning,
    stacklevel=2,
)

sys.modules["cbl_workflow"] = building_data_utilities
sys.modules["cbl_workflow.utils"] = building_data_utilities.utils
