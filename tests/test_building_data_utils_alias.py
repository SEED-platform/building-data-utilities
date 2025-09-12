# Do not move the imports in this file.


def test_bdu_workflow_import_triggers_deprecation():
    import importlib
    import sys
    import warnings

    import building_data_utilities  # ensure it's in sys.modules

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        importlib.reload(sys.modules["building_data_utilities"])
        assert any(issubclass(warning.category, DeprecationWarning) and "deprecated" in str(warning.message) for warning in w)
        # Check alias works
        assert hasattr(building_data_utilities, "utils")

        from building_data_utilities.utils import ubid

        assert hasattr(ubid, "add_ubid_to_geodataframe")
