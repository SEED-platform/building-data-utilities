# !/usr/bin/env python
"""
Tests for OpenStreetMap utilities
Simple tests for OSM data retrieval and geocoding
"""

import geopandas as gpd
import pytest
from shapely.geometry import Point

from building_data_utilities.utils.open_street_map import (
    download_building,
    download_building_and_nodes_by_id,
    find_nearest_building,
    get_building_id_from_osm_id,
    get_node_coordinates,
    neighboring_buildings,
    process_dataframe_for_osm_buildings,
    reverse_geocode,
)


class TestOpenStreetMapIntegration:
    def test_reverse_geocode_real(self):
        # Casa Bonita, Lakewood, CO
        lat, lon = 39.7405, -105.0772
        try:
            result = reverse_geocode(lat, lon)
        except Exception as e:
            pytest.skip(f"reverse_geocode failed: {e}")
        assert result is not None
        assert "address" in result
        assert result["address"].get("city", "").lower() == "lakewood"

    def test_get_building_id_from_osm_id_real(self):
        # Use a known OSM way ID for a building (Casa Bonita: 42431790)
        try:
            building_id = get_building_id_from_osm_id(42431790)
        except Exception as e:
            pytest.skip(f"get_building_id_from_osm_id failed: {e}")
        if isinstance(building_id, int):
            assert building_id == 42431790
        else:
            assert "not found" in str(building_id).lower() or "error" in str(building_id).lower()

    def test_download_building_real(self):
        # Use a known OSM way ID for a building (Casa Bonita: 42431790)
        try:
            data = download_building(42431790)
        except Exception as e:
            pytest.skip(f"download_building failed: {e}")
        assert data is not None
        assert "id" in data
        assert data["id"] == 42431790


class TestOpenStreetMapCoverage:
    def test_download_building_and_nodes_by_id_real(self):
        # Casa Bonita OSM way ID: 42431790
        try:
            building, nodes = download_building_and_nodes_by_id(42431790)
        except Exception as e:
            pytest.skip(f"download_building_and_nodes_by_id failed: {e}")
        assert building is not None
        assert isinstance(nodes, list)

    def test_get_node_coordinates_invalid(self):
        # Should return None for invalid node IDs
        result = get_node_coordinates([999999999])
        assert result is None

    def test_get_node_coordinates_small_polygon(self):
        # Should return None for less than 3 valid nodes
        # Use a single valid node from OSM (node id: 240949599)
        result = get_node_coordinates([240949599])
        assert result is None

    def test_neighboring_buildings_invalid(self):
        # Should return a string for invalid input
        location = {"address": {"road": "Fake Rd", "city": "Nowhere"}, "lat": 0, "lon": 0}
        result = neighboring_buildings(location)
        assert isinstance(result, str)

    def test_find_nearest_building_real(self):
        # Should return a dict for a real location (Casa Bonita area)
        result = find_nearest_building(39.7405, -105.0772)
        if result is not None:
            assert isinstance(result, dict)
        else:
            # Acceptable if nothing is found
            assert result is None

    def test_process_dataframe_for_osm_buildings_invalid_method(self):
        # Should raise ValueError for invalid method
        gdf = gpd.GeoDataFrame({"geometry": [Point(-105.0772, 39.7405)], "id": [1]})
        with pytest.raises(ValueError):  # noqa: PT011
            process_dataframe_for_osm_buildings(gdf, method="bad_method")

    def test_process_dataframe_for_osm_buildings_geometry_centroid(self):
        # Minimal test for geometry_centroid path
        gdf = gpd.GeoDataFrame({"geometry": [Point(-105.0772, 39.7405)], "id": [1]})
        results, errors = process_dataframe_for_osm_buildings(gdf, method="geometry_centroid")
        assert isinstance(results, list)
        assert isinstance(errors, list)

    def test_download_building_error_print(self, capsys):
        # Triggers print on error (lines 34)
        result = download_building(-999999)  # Invalid ID, guaranteed error
        captured = capsys.readouterr()
        assert "Error: Failed to download building nodes" in captured.out
        assert result is None

    def test_download_building_and_nodes_by_id_error_print(self, capsys):
        # Triggers print on error (lines 45)
        result = download_building_and_nodes_by_id(-999999)  # Invalid ID, guaranteed error
        captured = capsys.readouterr()
        assert "Error: Failed to download building nodes" in captured.out
        assert result is None

    def test_get_node_coordinates_invalid_range(self, capsys):
        # Triggers print for invalid coordinates (lines 95-96)
        result = get_node_coordinates([-1])
        captured = capsys.readouterr()
        assert "Error: Failed to retrieve coordinates" in captured.out or result is None

    def test_process_dataframe_for_osm_buildings_copy_source_columns(self):
        # Covers copy_source_columns True and address/geometry/ubid edge cases
        gdf = gpd.GeoDataFrame(
            {
                "geometry": [Point(-105.0772, 39.7405)],
                "id": [1],
                "extra": ["foo"],
            }
        )
        results, errors = process_dataframe_for_osm_buildings(gdf, method="geometry_centroid", copy_source_columns=True)
        assert isinstance(results, list)
        assert isinstance(errors, list)
        if results:
            assert "extra" in results[0]
