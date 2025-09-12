"""
SEED Platform (TM), Copyright (c) Alliance for Sustainable Energy, LLC, and other contributors.
See also https://github.com/SEED-platform/cbl-workflow/blob/main/LICENSE.md
"""

import warnings

from . import utils  # noqa: F401

warnings.warn(
    ("Importing 'building_data_utilities' is deprecated and will be removed in a future release."), DeprecationWarning, stacklevel=2
)
