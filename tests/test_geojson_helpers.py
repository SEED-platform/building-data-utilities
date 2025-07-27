# !/usr/bin/env python
"""
Tests for GeoJSON helper utilities
Simple tests for GeoJSON data manipulation
"""

from cbl_workflow.utils.geojson_helpers import extract_coordinates


class TestGeoJSONHelpers:
    """Simple tests for GeoJSON helper functions"""

    def test_extract_coordinates_basic_polygon(self):
        """Test extracting coordinates from a simple polygon GeoJSON"""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-105.0, 39.0], [-104.0, 39.0], [-104.0, 40.0], [-105.0, 40.0], [-105.0, 39.0]]],
                    },
                    "properties": {"name": "Test Polygon"},
                }
            ],
        }

        coordinates = extract_coordinates(geojson_data)

        # Should return a list with one coordinate array
        assert len(coordinates) == 1
        assert len(coordinates[0]) == 5  # 5 points (closed polygon)

        # Check first and last points are the same (closed polygon)
        assert coordinates[0][0] == coordinates[0][-1]

        # Check coordinate values
        assert coordinates[0][0] == [-105.0, 39.0]
        assert coordinates[0][1] == [-104.0, 39.0]

    def test_extract_coordinates_multiple_polygons(self):
        """Test extracting coordinates from multiple polygons"""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-105.0, 39.0], [-104.0, 39.0], [-104.0, 40.0], [-105.0, 40.0], [-105.0, 39.0]]],
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-103.0, 39.0], [-102.0, 39.0], [-102.0, 40.0], [-103.0, 40.0], [-103.0, 39.0]]],
                    },
                },
            ],
        }

        coordinates = extract_coordinates(geojson_data)

        # Should have coordinates from both polygons
        assert len(coordinates) == 2
        assert len(coordinates[0]) == 5
        assert len(coordinates[1]) == 5

        # Check that we got coordinates from both polygons
        assert coordinates[0][0] == [-105.0, 39.0]
        assert coordinates[1][0] == [-103.0, 39.0]

    def test_extract_coordinates_with_holes(self):
        """Test extracting coordinates from polygon with holes"""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            # Outer ring
                            [[-105.0, 39.0], [-104.0, 39.0], [-104.0, 40.0], [-105.0, 40.0], [-105.0, 39.0]],
                            # Inner ring (hole)
                            [[-104.8, 39.2], [-104.2, 39.2], [-104.2, 39.8], [-104.8, 39.8], [-104.8, 39.2]],
                        ],
                    },
                }
            ],
        }

        coordinates = extract_coordinates(geojson_data)

        # Should return both outer and inner rings
        assert len(coordinates) == 2  # outer ring + inner ring
        assert len(coordinates[0]) == 5  # outer ring points
        assert len(coordinates[1]) == 5  # inner ring points

    def test_extract_coordinates_mixed_geometries(self):
        """Test that only polygon coordinates are extracted"""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-104.5, 39.5]}},
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-105.0, 39.0], [-104.0, 39.0], [-104.0, 40.0], [-105.0, 40.0], [-105.0, 39.0]]],
                    },
                },
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[-104.0, 39.0], [-103.0, 40.0]]}},
            ],
        }

        coordinates = extract_coordinates(geojson_data)

        # Should only extract polygon coordinates, ignoring point and line
        assert len(coordinates) == 1
        assert len(coordinates[0]) == 5

    def test_extract_coordinates_empty_features(self):
        """Test extracting coordinates from empty feature collection"""
        geojson_data = {"type": "FeatureCollection", "features": []}

        coordinates = extract_coordinates(geojson_data)
        assert coordinates == []

    def test_extract_coordinates_no_polygons(self):
        """Test extracting coordinates when no polygons present"""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-104.5, 39.5]}},
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[-104.0, 39.0], [-103.0, 40.0]]}},
            ],
        }

        coordinates = extract_coordinates(geojson_data)
        assert coordinates == []

    def test_extract_coordinates_multipolygon_handling(self):
        """Test behavior with MultiPolygon (should be ignored)"""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [[[[-105.0, 39.0], [-104.0, 39.0], [-104.0, 40.0], [-105.0, 40.0], [-105.0, 39.0]]]],
                    },
                }
            ],
        }

        coordinates = extract_coordinates(geojson_data)
        # Current implementation only handles "Polygon", not "MultiPolygon"
        assert coordinates == []

    def test_extract_coordinates_real_world_structure(self):
        """Test with a more realistic GeoJSON structure"""
        geojson_data = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 1, "building_type": "residential", "area": 1500.0},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-104.9903, 39.7392], [-104.9883, 39.7392], [-104.9883, 39.7412], [-104.9903, 39.7412], [-104.9903, 39.7392]]
                        ],
                    },
                }
            ],
        }

        coordinates = extract_coordinates(geojson_data)

        assert len(coordinates) == 1
        assert len(coordinates[0]) == 5
        # Check precision is preserved
        assert coordinates[0][0] == [-104.9903, 39.7392]
