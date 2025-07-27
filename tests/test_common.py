# !/usr/bin/env python
"""
Tests for common utilities and types
Simple tests for shared data structures
"""

from cbl_workflow.utils.common import Location


class TestCommonTypes:
    """Simple tests for common data types and utilities"""

    def test_location_type_basic(self):
        """Test basic Location type usage"""
        # Create a Location
        location = Location(street="123 Main St", city="Denver", state="CO")

        # Check that it has the expected fields
        assert location["street"] == "123 Main St"
        assert location["city"] == "Denver"
        assert location["state"] == "CO"

    def test_location_type_dict_access(self):
        """Test that Location works like a dictionary"""
        location = Location(street="456 Oak Ave", city="Boulder", state="CO")

        # Test dictionary-style access
        assert location.get("street") == "456 Oak Ave"
        assert location.get("city") == "Boulder"
        assert location.get("state") == "CO"
        assert location.get("nonexistent") is None

        # Test key existence
        assert "street" in location
        assert "city" in location
        assert "state" in location
        assert "zipcode" not in location

    def test_location_type_iteration(self):
        """Test that Location can be iterated over"""
        location = Location(street="789 Pine St", city="Colorado Springs", state="CO")

        # Test iteration
        keys = list(location.keys())
        assert "street" in keys
        assert "city" in keys
        assert "state" in keys
        assert len(keys) == 3

        # Test values
        values = list(location.values())
        assert "789 Pine St" in values
        assert "Colorado Springs" in values
        assert "CO" in values

    def test_location_type_update(self):
        """Test that Location can be updated like a dict"""
        location = Location(street="111 Test St", city="Test City", state="TX")

        # Update values
        location["city"] = "Updated City"
        location["state"] = "CA"

        assert location["city"] == "Updated City"
        assert location["state"] == "CA"
        assert location["street"] == "111 Test St"  # Unchanged

    def test_location_type_from_dict(self):
        """Test creating Location from dictionary"""
        data = {"street": "222 Example Rd", "city": "Example City", "state": "NY"}

        # Create Location from dict
        location = Location(**data)

        assert location["street"] == "222 Example Rd"
        assert location["city"] == "Example City"
        assert location["state"] == "NY"

    def test_location_type_equality(self):
        """Test Location equality comparison"""
        location1 = Location(street="333 Same St", city="Same City", state="FL")

        location2 = Location(street="333 Same St", city="Same City", state="FL")

        location3 = Location(street="444 Different St", city="Same City", state="FL")

        # Test equality
        assert location1 == location2
        assert location1 != location3

    def test_location_type_copy(self):
        """Test copying Location objects"""
        original = Location(street="555 Original St", city="Original City", state="WA")

        # Create a copy and modify it
        copy = original.copy()
        copy["street"] = "555 Modified St"

        # Original should be unchanged
        assert original["street"] == "555 Original St"
        assert copy["street"] == "555 Modified St"
        assert original["city"] == copy["city"]  # Other fields same

    def test_location_type_required_fields(self):
        """Test that Location requires all expected fields"""
        # This should work (all required fields present)
        complete_location = Location(street="666 Complete St", city="Complete City", state="OR")
        assert complete_location is not None

        # Test that we can create partial locations if needed
        # (TypedDict doesn't enforce required fields at runtime,
        #  but this shows the expected structure)
        partial_data = {"street": "777 Partial St"}
        try:
            # This might work at runtime but would be flagged by type checker
            partial_location = Location(**partial_data)
            # If it works, just check that the field is there
            assert partial_location["street"] == "777 Partial St"
        except TypeError:
            # If it fails, that's also valid behavior
            pass

    def test_location_type_string_representation(self):
        """Test string representation of Location"""
        location = Location(street="888 String St", city="String City", state="ID")

        # Convert to string and check it contains the data
        location_str = str(location)
        assert "888 String St" in location_str
        assert "String City" in location_str
        assert "ID" in location_str

    def test_location_type_list_usage(self):
        """Test using Location in a list (common use case)"""
        locations = [
            Location(street="100 First St", city="City1", state="CA"),
            Location(street="200 Second St", city="City2", state="CA"),
            Location(street="300 Third St", city="City3", state="CA"),
        ]

        # Test list operations
        assert len(locations) == 3
        assert locations[0]["street"] == "100 First St"
        assert locations[1]["city"] == "City2"
        assert locations[2]["state"] == "CA"

        # Test filtering
        city1_locations = [loc for loc in locations if loc["city"] == "City1"]
        assert len(city1_locations) == 1
        assert city1_locations[0]["street"] == "100 First St"
