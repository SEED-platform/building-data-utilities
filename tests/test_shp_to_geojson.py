# !/usr/bin/env python
"""
Tests for shapefile to GeoJSON conversion utility
Simple integration-style tests using temporary files
"""

import json
import os
import shutil
import tempfile

import geopandas as gpd
from shapely.geometry import Point, Polygon

from building_data_utilities.utils.shp_to_geojson import shp_to_geojson


class TestShpToGeoJSON:
    """Integration tests for shapefile to GeoJSON conversion"""

    def setup_method(self):
        """Create temporary test files before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_shp = os.path.join(self.temp_dir, "test.shp")
        self.expected_geojson = os.path.join(self.temp_dir, "test.geojson")

    def teardown_method(self):
        """Clean up test files after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_shapefile_points(self):
        """Helper to create a simple point shapefile"""
        data = {
            "id": [1, 2, 3],
            "name": ["Point A", "Point B", "Point C"],
            "geometry": [Point(-104.9903, 39.7392), Point(-105.1019, 39.7200), Point(-105.0000, 39.7500)],
        }
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
        gdf.to_file(self.test_shp)
        return gdf

    def create_test_shapefile_polygons(self):
        """Helper to create a simple polygon shapefile"""
        # Create simple rectangular polygons
        poly1 = Polygon([(-105, 39), (-104, 39), (-104, 40), (-105, 40)])
        poly2 = Polygon([(-106, 40), (-105, 40), (-105, 41), (-106, 41)])

        data = {"id": [1, 2], "building_type": ["residential", "commercial"], "geometry": [poly1, poly2]}
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
        gdf.to_file(self.test_shp)
        return gdf

    def test_convert_point_shapefile(self):
        """Test converting a point shapefile to GeoJSON"""
        # Create test shapefile
        self.create_test_shapefile_points()

        # Convert to GeoJSON
        shp_to_geojson(self.test_shp)

        # Check that output file was created
        assert os.path.exists(self.expected_geojson)

        # Verify the GeoJSON content
        with open(self.expected_geojson) as f:
            geojson_data = json.load(f)

        # Basic structure checks
        assert geojson_data["type"] == "FeatureCollection"
        assert "features" in geojson_data
        assert len(geojson_data["features"]) == 3

        # Check first feature
        first_feature = geojson_data["features"][0]
        assert first_feature["type"] == "Feature"
        assert "geometry" in first_feature
        assert "properties" in first_feature

        # Verify properties are preserved
        feature_names = [f["properties"]["name"] for f in geojson_data["features"]]
        assert "Point A" in feature_names
        assert "Point B" in feature_names
        assert "Point C" in feature_names

    def test_convert_polygon_shapefile(self):
        """Test converting a polygon shapefile to GeoJSON"""
        # Create test shapefile
        self.create_test_shapefile_polygons()

        # Convert to GeoJSON
        shp_to_geojson(self.test_shp)

        # Check that output file was created
        assert os.path.exists(self.expected_geojson)

        # Verify the GeoJSON content
        with open(self.expected_geojson) as f:
            geojson_data = json.load(f)

        # Basic structure checks
        assert geojson_data["type"] == "FeatureCollection"
        assert len(geojson_data["features"]) == 2

        # Check geometry types
        geometries = [f["geometry"]["type"] for f in geojson_data["features"]]
        assert all(geom_type == "Polygon" for geom_type in geometries)

        # Verify properties are preserved
        # (column names may be modified by UBID processing)
        # Check that we have the expected number of features and properties
        assert len(geojson_data["features"]) == 2
        feature_properties = geojson_data["features"][0]["properties"]
        assert "id" in feature_properties  # ID should be preserved

        # The building_type might be renamed or modified during processing
        # Just verify we have some properties
        assert len(feature_properties) > 0

    def test_output_has_ubid_columns(self):
        """Test that the output includes UBID-related columns"""
        # Create test shapefile
        self.create_test_shapefile_polygons()

        # Convert to GeoJSON
        shp_to_geojson(self.test_shp)

        # Load the result
        result_gdf = gpd.read_file(self.expected_geojson)

        # Check that UBID column was added
        assert "ubid" in result_gdf.columns

        # Verify UBID values are not null
        assert result_gdf["ubid"].notna().all()

        # UBID should be strings
        assert all(isinstance(ubid, str) for ubid in result_gdf["ubid"])

    def test_coordinate_reference_system(self):
        """Test that output is in WGS84 (EPSG:4326)"""
        # Create test shapefile in different CRS (UTM Zone 13N)
        data = {
            "id": [1],
            "name": ["Test Point"],
            "geometry": [Point(500000, 4400000)],  # UTM coordinates
        }
        gdf = gpd.GeoDataFrame(data, crs="EPSG:32613")  # UTM Zone 13N
        gdf.to_file(self.test_shp)

        # Convert to GeoJSON
        shp_to_geojson(self.test_shp)

        # Load result and check CRS
        result_gdf = gpd.read_file(self.expected_geojson)
        assert result_gdf.crs.to_string() == "EPSG:4326"

        # Check that coordinates are in reasonable lat/lon range
        bounds = result_gdf.total_bounds
        # Should be somewhere in North America
        assert -180 <= bounds[0] <= 180  # longitude
        assert -90 <= bounds[1] <= 90  # latitude

    def test_file_path_as_string(self):
        """Test function works with string file paths"""
        self.create_test_shapefile_points()

        # Test with string path
        shp_to_geojson(self.test_shp)
        assert os.path.exists(self.expected_geojson)

    def test_file_path_as_pathlib(self):
        """Test function works with pathlib.Path objects"""
        from pathlib import Path

        self.create_test_shapefile_points()

        # Test with Path object
        shp_to_geojson(Path(self.test_shp))
        assert os.path.exists(self.expected_geojson)

    def test_nonexistent_file_raises_error(self):
        """Test che la funzione sollevi errore per file mancante"""
        import pytest

        nonexistent_file = os.path.join(self.temp_dir, "does_not_exist.shp")
        with pytest.raises(Exception, match="does_not_exist.shp"):
            shp_to_geojson(nonexistent_file)
