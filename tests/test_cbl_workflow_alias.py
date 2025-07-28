import warnings

# Test that importing cbl_workflow triggers a deprecation warning and works as an alias


def test_cbl_workflow_import_triggers_deprecation():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import cbl_workflow

        assert any(issubclass(warning.category, DeprecationWarning) and "deprecated" in str(warning.message) for warning in w)
        # Check alias works
        assert hasattr(cbl_workflow, "utils")
        from cbl_workflow.utils import ubid

        assert hasattr(ubid, "add_ubid_to_geodataframe")
