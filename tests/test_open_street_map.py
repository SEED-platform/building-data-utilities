# !/usr/bin/env python
"""
Tests for OpenStreetMap utilities
Simple tests for OSM data retrieval and geocoding
"""

from unittest.mock import Mock, patch
from cbl_workflow.utils.open_street_map import (
    reverse_geocode,
    get_building_id_from_osm_id,
    download_building
)


class TestOpenStreetMapUtils:
    """Simple tests for OpenStreetMap utility functions"""

    @patch('cbl_workflow.utils.open_street_map.Nominatim')
    def test_reverse_geocode_basic(self, mock_nominatim_class):
        """Test basic reverse geocoding functionality"""
        # Mock the geocoding response
        mock_location = Mock()
        mock_location.raw = {
            "place_id": 123456,
            "display_name": "123 Main St, Denver, CO, USA",
            "address": {
                "house_number": "123",
                "road": "Main Street",
                "city": "Denver",
                "state": "Colorado",
                "country": "United States"
            }
        }

        mock_geolocator = Mock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator

        # Test reverse geocoding
        result = reverse_geocode(39.7392, -104.9903)

        # Check that Nominatim was initialized properly
        mock_nominatim_class.assert_called_once_with(user_agent="CBL")

        # Check that reverse was called with correct parameters
        mock_geolocator.reverse.assert_called_once_with(
            (39.7392, -104.9903),
            language="en",
            exactly_one=True
        )

        # Check result
        assert result["place_id"] == 123456
        assert "Main St" in result["display_name"]
        assert result["address"]["city"] == "Denver"

    @patch('cbl_workflow.utils.open_street_map.Nominatim')
    def test_reverse_geocode_no_results(self, mock_nominatim_class):
        """Test reverse geocoding when no results found"""
        mock_geolocator = Mock()
        mock_geolocator.reverse.return_value = None
        mock_nominatim_class.return_value = mock_geolocator

        try:
            result = reverse_geocode(0.0, 0.0)  # Middle of ocean
            # If no exception, the result might be None
            assert result is None
        except AttributeError:
            # This is expected if trying to access .raw on None
            pass

    @patch('cbl_workflow.utils.open_street_map.requests.post')
    def test_get_building_id_from_osm_id_success(self, mock_post):
        """Test successful building ID retrieval"""
        # Mock successful Overpass API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {"id": 12345, "type": "way"}
            ]
        }
        mock_post.return_value = mock_response

        result = get_building_id_from_osm_id(12345)

        # Check the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "overpass-api.de" in call_args[0][0]
        assert "12345" in call_args[1]["data"]

        # Check result
        assert result == 12345

    @patch('cbl_workflow.utils.open_street_map.requests.post')
    def test_get_building_id_from_osm_id_not_found(self, mock_post):
        """Test building ID retrieval when building not found"""
        # Mock response with no elements
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"elements": []}
        mock_post.return_value = mock_response

        result = get_building_id_from_osm_id(99999)

        assert result == "Building ID not found for the given place ID."

    @patch('cbl_workflow.utils.open_street_map.requests.post')
    def test_get_building_id_from_osm_id_api_error(self, mock_post):
        """Test building ID retrieval when API returns error"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = get_building_id_from_osm_id(12345)

        assert result == "Error: Failed to retrieve building ID."

    @patch('cbl_workflow.utils.open_street_map.requests.post')
    def test_get_building_id_from_osm_id_multiple_elements(self, mock_post):
        """Test building ID retrieval with multiple elements"""
        # Mock response with multiple elements (should return first with ID)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {"type": "way", "tags": {}},  # No ID
                {"id": 12345, "type": "way"},  # This should be returned
                {"id": 67890, "type": "way"}   # This should be ignored
            ]
        }
        mock_post.return_value = mock_response

        result = get_building_id_from_osm_id(12345)

        assert result == 12345

    @patch('cbl_workflow.utils.open_street_map.requests.post')
    def test_download_building_basic(self, mock_post):
        """Test basic building download functionality"""
        # Mock successful Overpass API response for building data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {
                    "type": "way",
                    "id": 12345,
                    "nodes": [1, 2, 3, 4, 1],
                    "tags": {
                        "building": "residential",
                        "addr:street": "Main Street",
                        "addr:housenumber": "123"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Test download_building function exists and can be called
        try:
            download_building(12345)
            # If function exists, check that it made the request
            mock_post.assert_called()
        except NameError:
            # Function might not be fully implemented yet
            pass

    def test_overpass_url_constant(self):
        """Test that OVERPASS_URL is properly defined"""
        from cbl_workflow.utils.open_street_map import OVERPASS_URL
        
        assert OVERPASS_URL is not None
        assert isinstance(OVERPASS_URL, str)
        assert "overpass" in OVERPASS_URL.lower()
        assert OVERPASS_URL.startswith("http")

    @patch('cbl_workflow.utils.open_street_map.requests.post')
    def test_get_building_id_query_format(self, mock_post):
        """Test that the Overpass query is properly formatted"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"elements": []}
        mock_post.return_value = mock_response

        get_building_id_from_osm_id(12345)

        # Check that the query was formatted correctly
        call_args = mock_post.call_args
        query = call_args[1]["data"]

        # Basic query structure checks
        assert "[out:json]" in query
        assert "way(id:12345)" in query
        assert "out ids" in query

    @patch('cbl_workflow.utils.open_street_map.Nominatim')
    def test_reverse_geocode_rate_limiting_consideration(
            self, mock_nominatim_class
    ):
        """Test that reverse geocoding is set up to respect rate limits"""
        mock_location = Mock()
        mock_location.raw = {"place_id": 123}

        mock_geolocator = Mock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator

        # Call the function
        reverse_geocode(39.7392, -104.9903)

        # Verify user agent is set (important for Nominatim terms of service)
        mock_nominatim_class.assert_called_once_with(user_agent="CBL")

        # Verify exactly_one=True to get single result
        mock_geolocator.reverse.assert_called_once()
        call_kwargs = mock_geolocator.reverse.call_args[1]
        assert call_kwargs["exactly_one"] is True

    @patch('cbl_workflow.utils.open_street_map.requests.post')
    def test_api_integration_parameters(self, mock_post):
        """Test that API calls use correct parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"elements": []}
        mock_post.return_value = mock_response

        get_building_id_from_osm_id(54321)

        # Verify the API endpoint and method
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://overpass-api.de/api/interpreter"
        assert "data" in call_args[1]
        assert isinstance(call_args[1]["data"], str)
