# !/usr/bin/env python
"""
Tests for geocoding address utilities
Simple tests for address geocoding functionality
"""

from unittest.mock import Mock, patch
from cbl_workflow.utils.geocode_addresses import (
    _process_result,
    geocode_addresses,
    MapQuestAPIKeyError
)
from cbl_workflow.utils.common import Location


class TestGeocodeAddresses:
    """Simple tests for geocoding functionality"""

    def test_process_result_single_valid_location(self):
        """Test processing a valid single geocoding result"""
        # Mock a valid MapQuest response
        mock_result = {
            "locations": [{
                "geocodeQualityCode": "P1AAA",  # Point-level, high confidence
                "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                "street": "123 Main St",
                "postalCode": "80202",
                "sideOfStreet": "R",
                "adminArea1": "US",
                "adminArea1Type": "Country",
                "adminArea3": "Denver",
                "adminArea3Type": "City",
                "adminArea4": "Denver County",
                "adminArea4Type": "County",
                "adminArea5": "CO",
                "adminArea5Type": "State"
            }]
        }

        result = _process_result(mock_result)

        # Check basic structure
        assert "quality" in result
        assert "latitude" in result
        assert "longitude" in result
        assert "address" in result

        # Check values
        assert result["quality"] == "P1AAA"
        assert result["latitude"] == 39.7392
        assert result["longitude"] == -104.9903
        assert result["address"] == "123 Main St"
        assert result["postal_code"] == "80202"

        # Check admin areas were flattened
        assert result["country"] == "US"
        assert result["city"] == "Denver"
        assert result["state"] == "CO"

    def test_process_result_multiple_locations(self):
        """Test processing result with multiple locations (ambiguous)"""
        mock_result = {
            "locations": [
                {"geocodeQualityCode": "P1AAA"},
                {"geocodeQualityCode": "P1AAA"}
            ]
        }

        result = _process_result(mock_result)
        assert result["quality"] == "Ambiguous"

    def test_process_result_low_quality(self):
        """Test processing result with low quality geocoding"""
        mock_result = {
            "locations": [{
                "geocodeQualityCode": "A5CCC",  # Low confidence
                "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                "street": "123 Main St"
            }]
        }

        result = _process_result(mock_result)
        # Should return quality but not accept the location
        assert result["quality"] == "A5CCC"
        assert "latitude" not in result
        assert "longitude" not in result

    def test_process_result_unacceptable_granularity(self):
        """Test processing result with unacceptable granularity level"""
        mock_result = {
            "locations": [{
                "geocodeQualityCode": "Z1AAA",  # Bad granularity
                "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                "street": "123 Main St"
            }]
        }

        result = _process_result(mock_result)
        assert result["quality"] == "Z1AAA"
        assert "latitude" not in result

    def test_process_result_confidence_with_c_or_x(self):
        """Test processing result with C or X in confidence rating"""
        mock_result = {
            "locations": [{
                "geocodeQualityCode": "P1ACX",  # Has C and X
                "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                "street": "123 Main St"
            }]
        }

        result = _process_result(mock_result)
        assert result["quality"] == "P1ACX"
        assert "latitude" not in result

    @patch('cbl_workflow.utils.geocode_addresses.requests.post')
    def test_geocode_addresses_success(self, mock_post):
        """Test successful geocoding of addresses"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "locations": [{
                    "geocodeQualityCode": "P1AAA",
                    "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                    "street": "123 Main St",
                    "postalCode": "80202",
                    "adminArea3": "Denver",
                    "adminArea3Type": "City",
                    "adminArea5": "CO",
                    "adminArea5Type": "State"
                }]
            }]
        }
        mock_post.return_value = mock_response

        # Test data
        locations = [
            Location(street="123 Main St", city="Denver", state="CO")
        ]

        # Geocode
        results = geocode_addresses(locations, "fake_api_key")

        # Check results
        assert len(results) == 1
        assert results[0]["latitude"] == 39.7392
        assert results[0]["longitude"] == -104.9903
        assert results[0]["quality"] == "P1AAA"

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "mapquestapi.com" in call_args[0][0]
        assert "fake_api_key" in call_args[0][0]

    @patch('cbl_workflow.utils.geocode_addresses.requests.post')
    def test_geocode_addresses_invalid_api_key_401(self, mock_post):
        """Test handling of invalid API key (401 error)"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.content = b"Invalid API key"
        mock_post.return_value = mock_response

        locations = [
            Location(street="123 Main St", city="Denver", state="CO")
        ]

        try:
            geocode_addresses(locations, "invalid_key")
            assert False, "Expected MapQuestAPIKeyError"
        except MapQuestAPIKeyError as e:
            assert "API Key is invalid" in str(e)

    @patch('cbl_workflow.utils.geocode_addresses.requests.post')
    def test_geocode_addresses_api_limit_403(self, mock_post):
        """Test handling of API limit exceeded (403 error)"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        locations = [
            Location(street="123 Main St", city="Denver", state="CO")
        ]

        try:
            geocode_addresses(locations, "limited_key")
            assert False, "Expected MapQuestAPIKeyError"
        except MapQuestAPIKeyError as e:
            assert "at its limit" in str(e)

    @patch('cbl_workflow.utils.geocode_addresses.requests.post')
    def test_geocode_addresses_chunking(self, mock_post):
        """Test that large lists are properly chunked"""
        # Mock response for each chunk - each response contains results for
        # ALL locations in that chunk
        def mock_response_generator(*args, **kwargs):
            # Get the locations from the request
            locations_in_request = kwargs.get('json', {}).get('locations', [])
            results = []
            for _ in locations_in_request:
                results.append({
                    "locations": [{
                        "geocodeQualityCode": "P1AAA",
                        "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                        "street": "123 Main St"
                    }]
                })
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": results}
            return mock_response

        mock_post.side_effect = mock_response_generator

        # Create more than 100 locations to test chunking
        locations = []
        for i in range(150):
            locations.append(
                Location(
                    street=f"{i} Test St",
                    city="Denver",
                    state="CO"
                )
            )

        results = geocode_addresses(locations, "test_key")

        # Should have results for all locations
        assert len(results) == 150

        # Should have made multiple API calls due to chunking
        assert mock_post.call_count == 2  # 150 locations = 2 chunks

    def test_geocode_addresses_empty_list(self):
        """Test geocoding with empty location list"""
        results = geocode_addresses([], "test_key")
        assert results == []

    @patch('cbl_workflow.utils.geocode_addresses.requests.post')
    def test_geocode_addresses_mixed_quality_results(self, mock_post):
        """Test geocoding with mixed quality results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {  # Good result
                    "locations": [{
                        "geocodeQualityCode": "P1AAA",
                        "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                        "street": "123 Main St"
                    }]
                },
                {  # Poor quality result
                    "locations": [{
                        "geocodeQualityCode": "A5CCC",
                        "displayLatLng": {"lng": -104.9903, "lat": 39.7392},
                        "street": "456 Oak St"
                    }]
                },
                {  # Ambiguous result
                    "locations": [
                        {"geocodeQualityCode": "P1AAA"},
                        {"geocodeQualityCode": "P1AAA"}
                    ]
                }
            ]
        }
        mock_post.return_value = mock_response

        locations = [
            Location(street="123 Main St", city="Denver", state="CO"),
            Location(street="456 Oak St", city="Denver", state="CO"),
            Location(street="789 Pine St", city="Denver", state="CO")
        ]

        results = geocode_addresses(locations, "test_key")

        assert len(results) == 3
        # First result should have coordinates
        assert "latitude" in results[0]
        assert "longitude" in results[0]
        # Second result should not (poor quality)
        assert "latitude" not in results[1]
        # Third result should be ambiguous
        assert results[2]["quality"] == "Ambiguous"
