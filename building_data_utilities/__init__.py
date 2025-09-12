import warnings

from . import utils  # noqa: F401

warnings.warn(
    ("Importing 'building_data_utilities' is deprecated and will be removed in a future release."), DeprecationWarning, stacklevel=2
)
