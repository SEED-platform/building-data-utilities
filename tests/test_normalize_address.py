# !/usr/bin/env python
"""
Tests for address normalization utilities
Simple integration-style tests that are easy to understand
"""

from building_data_utilities.utils.normalize_address import (
    _normalize_address_direction,
    _normalize_address_number,
    _normalize_address_post_type,
    _normalize_occupancy_type,
    _normalize_subaddress_type,
    normalize_address,
)


class TestAddressNormalization:
    """Simple tests for address normalization functions"""

    def test_normalize_subaddress_type_basic(self):
        """Test building type normalization - common abbreviations"""
        assert _normalize_subaddress_type("bldg") == "building"
        assert _normalize_subaddress_type("BLDG") == "building"
        assert _normalize_subaddress_type("blg") == "building"
        assert _normalize_subaddress_type("tower") == "tower"  # no mapping
        assert _normalize_subaddress_type("bldg.") == "building"  # with period

    def test_normalize_occupancy_type_basic(self):
        """Test suite/unit type normalization"""
        assert _normalize_occupancy_type("ste") == "suite"
        assert _normalize_occupancy_type("STE") == "suite"
        assert _normalize_occupancy_type("suite") == "suite"
        assert _normalize_occupancy_type("unit") == "unit"  # no mapping
        assert _normalize_occupancy_type("ste.") == "suite"  # with period

    def test_normalize_direction_basic(self):
        """Test direction abbreviation - all cardinal directions"""
        # Basic directions
        assert _normalize_address_direction("north") == "n"
        assert _normalize_address_direction("SOUTH") == "s"
        assert _normalize_address_direction("east") == "e"
        assert _normalize_address_direction("west") == "w"

        # Compound directions
        assert _normalize_address_direction("northeast") == "ne"
        assert _normalize_address_direction("northwest") == "nw"
        assert _normalize_address_direction("southeast") == "se"
        assert _normalize_address_direction("southwest") == "sw"

        # Already abbreviated
        assert _normalize_address_direction("n") == "n"
        assert _normalize_address_direction("ne") == "ne"

    def test_normalize_post_type_basic(self):
        """Test street type normalization"""
        assert _normalize_address_post_type("avenue") == "ave"
        assert _normalize_address_post_type("AVENUE") == "ave"
        assert _normalize_address_post_type("street") == "street"  # no mapping
        assert _normalize_address_post_type("avenue.") == "ave"  # with period

    def test_normalize_address_number_basic(self):
        """Test address number normalization - leading zeros and ranges"""
        # Basic number
        assert _normalize_address_number("123") == "123"

        # Leading zeros
        assert _normalize_address_number("0123") == "123"
        assert _normalize_address_number("00456") == "456"

        # Single digit with leading zero
        assert _normalize_address_number("05") == "5"

    def test_normalize_address_number_ranges(self):
        """Test address number ranges with different separators"""
        # Note: The regex in the code has some issues, but we test what
        # it should do. These tests may fail with the current regex -
        # they show expected behavior
        try:
            # Dash separator
            result = _normalize_address_number("123-125")
            assert result == "123-125"

            # Slash separator
            result = _normalize_address_number("123/125")
            assert result == "123-125"
        except Exception as e:
            import pytest

            pytest.fail(f"_normalize_address_number ha sollevato un'eccezione inattesa: {e}")

    def test_normalize_address_full_integration(self):
        """Integration test - full address normalization"""
        # Simple address
        result = normalize_address("123 Main St")
        assert result is not None
        assert "123" in result
        assert "main" in result
        assert "st" in result

        # Address with suite
        result = normalize_address("456 Oak Ave Suite 100")
        assert result is not None
        assert "456" in result
        assert "oak" in result
        assert "suite" in result
        assert "100" in result

        # Address with direction
        result = normalize_address("789 Elm St NW")
        assert result is not None
        assert "789" in result
        assert "elm" in result
        assert "nw" in result

    def test_normalize_address_edge_cases(self):
        """Test edge cases and error handling"""
        # Empty string
        assert normalize_address("") is None
        assert normalize_address(None) is None

        # Bytes input
        result = normalize_address(b"123 Main St")
        assert result is not None
        assert "123" in result
        assert "main" in result

        # Non-string input
        result = normalize_address(123)
        assert result is not None

    def test_normalize_address_special_characters(self):
        """Test handling of special characters"""
        # Unicode replacement character
        result = normalize_address("123 Main St\ufffd")
        assert result is not None
        assert "123" in result
        assert "main" in result

        # Other special characters
        result = normalize_address("123 Main St\xef\xbf\xbd")
        assert result is not None
        assert "123" in result
        assert "main" in result
