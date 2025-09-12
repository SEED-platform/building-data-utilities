import warnings

# Test that importing building_data_utilities triggers a deprecation warning and works as an alias


def test_bdu_workflow_import_triggers_deprecation():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import building_data_utilities

        assert any(issubclass(warning.category, DeprecationWarning) and "deprecated" in str(warning.message) for warning in w)
        # Check alias works
        assert hasattr(building_data_utilities, "utils")
        from building_data_utilities.utils import ubid

        assert hasattr(ubid, "add_ubid_to_geodataframe")
