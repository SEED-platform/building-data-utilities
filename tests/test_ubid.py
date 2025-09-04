# !/usr/bin/env python
"""
Tests for UBID (Unique Building Identifier) utilities
Simple tests for encoding/decoding and GeoDataFrame operations
"""

import geopandas as gpd
from shapely.geometry import Point, Polygon

from building_data_utilities.utils.ubid import add_ubid_to_geodataframe, bounding_box, centroid, encode_ubid


class TestUBIDUtils:
    """Simple tests for UBID utility functions"""

    def test_encode_ubid_basic(self):
        """Test basic UBID encoding for a simple polygon"""
        # Create a simple square polygon
        coords = [(-105, 39), (-104, 39), (-104, 40), (-105, 40), (-105, 39)]
        polygon = Polygon(coords)

        # Encode UBID
        ubid = encode_ubid(polygon)

        # Basic checks
        assert isinstance(ubid, str)
        assert len(ubid) > 0
        # UBID should contain at least some expected characters
        assert any(c in ubid for c in "23456789CFGHJMPQRVWX")

    def test_encode_ubid_with_custom_length(self):
        """Test UBID encoding with different code lengths"""
        coords = [(-105, 39), (-104, 39), (-104, 40), (-105, 40), (-105, 39)]
        polygon = Polygon(coords)

        # Test different code lengths
        ubid_10 = encode_ubid(polygon, code_length=10)
        ubid_12 = encode_ubid(polygon, code_length=12)

        assert isinstance(ubid_10, str)
        assert isinstance(ubid_12, str)
        # Longer code should be longer or equal
        assert len(ubid_12) >= len(ubid_10)

    def test_bounding_box_basic(self):
        """Test UBID bounding box extraction"""
        # Create test polygon and get its UBID
        coords = [(-105, 39), (-104, 39), (-104, 40), (-105, 40), (-105, 39)]
        polygon = Polygon(coords)
        ubid = encode_ubid(polygon)

        # Get bounding box
        bbox = bounding_box(ubid)

        # Check result is a polygon
        assert isinstance(bbox, Polygon)

        # Check bounding box makes sense
        bounds = bbox.bounds
        assert len(bounds) == 4  # minx, miny, maxx, maxy

        # Bounding box should roughly contain the original area
        # (allowing for UBID approximation)
        original_bounds = polygon.bounds
        bbox_center_x = (bounds[0] + bounds[2]) / 2
        bbox_center_y = (bounds[1] + bounds[3]) / 2
        orig_center_x = (original_bounds[0] + original_bounds[2]) / 2
        orig_center_y = (original_bounds[1] + original_bounds[3]) / 2

        # Centers should be reasonably close
        assert abs(bbox_center_x - orig_center_x) < 1.0
        assert abs(bbox_center_y - orig_center_y) < 1.0

    def test_centroid_basic(self):
        """Test UBID centroid extraction"""
        # Create test polygon and get its UBID
        coords = [(-105, 39), (-104, 39), (-104, 40), (-105, 40), (-105, 39)]
        polygon = Polygon(coords)
        ubid = encode_ubid(polygon)

        # Get centroid
        center = centroid(ubid)

        # Check result is a point
        assert isinstance(center, Point)

        # Check coordinates are reasonable
        assert -180 <= center.x <= 180
        assert -90 <= center.y <= 90

        # Centroid should be roughly in the middle of our test area
        assert -106 <= center.x <= -103
        assert 38 <= center.y <= 41

    def test_add_ubid_to_geodataframe_basic(self):
        """Test adding UBID to a simple GeoDataFrame"""
        # Create test GeoDataFrame with polygons
        polygons = [Polygon([(-105, 39), (-104, 39), (-104, 40), (-105, 40)]), Polygon([(-103, 39), (-102, 39), (-102, 40), (-103, 40)])]
        data = {"id": [1, 2], "name": ["Building A", "Building B"], "geometry": polygons}
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

        # Add UBID
        result_gdf = add_ubid_to_geodataframe(gdf)

        # Check that UBID column was added
        assert "ubid" in result_gdf.columns
        assert len(result_gdf) == 2

        # Check UBID values
        assert result_gdf["ubid"].notna().all()
        assert all(isinstance(ubid, str) for ubid in result_gdf["ubid"])
        assert all(len(ubid) > 0 for ubid in result_gdf["ubid"])

        # Original columns should still be there
        assert "id" in result_gdf.columns
        assert "name" in result_gdf.columns
        assert "geometry" in result_gdf.columns

    def test_add_ubid_with_additional_columns(self):
        """Test adding UBID with additional centroid and bbox columns"""
        # Create test GeoDataFrame
        polygon = Polygon([(-105, 39), (-104, 39), (-104, 40), (-105, 40)])
        gdf = gpd.GeoDataFrame({"id": [1], "geometry": [polygon]}, crs="EPSG:4326")

        # Add UBID with additional columns
        result_gdf = add_ubid_to_geodataframe(gdf, additional_ubid_columns_to_create=["ubid_centroid", "ubid_bbox"])

        # Check all expected columns are present
        assert "ubid" in result_gdf.columns
        assert "ubid_centroid" in result_gdf.columns
        assert "ubid_bbox" in result_gdf.columns

        # Check centroid column
        centroid_geom = result_gdf["ubid_centroid"].iloc[0]
        assert isinstance(centroid_geom, Point)

        # Check bbox column
        bbox_geom = result_gdf["ubid_bbox"].iloc[0]
        assert isinstance(bbox_geom, Polygon)

    def test_add_ubid_with_points(self):
        """Test adding UBID to a GeoDataFrame with point geometries"""
        # Create test GeoDataFrame with points
        points = [Point(-104.5, 39.5), Point(-102.5, 39.5)]
        gdf = gpd.GeoDataFrame({"id": [1, 2], "geometry": points}, crs="EPSG:4326")

        # Add UBID - this should work even with points
        result_gdf = add_ubid_to_geodataframe(gdf)

        # Check results
        assert "ubid" in result_gdf.columns
        assert len(result_gdf) == 2
        assert result_gdf["ubid"].notna().all()

    def test_add_ubid_preserves_crs(self):
        """Test that adding UBID preserves the original CRS"""
        # Create test GeoDataFrame in different CRS
        polygon = Polygon([(-105, 39), (-104, 39), (-104, 40), (-105, 40)])
        gdf = gpd.GeoDataFrame({"id": [1], "geometry": [polygon]}, crs="EPSG:4326")

        # Add UBID
        result_gdf = add_ubid_to_geodataframe(gdf)

        # Check CRS is preserved
        assert result_gdf.crs == gdf.crs

    def test_add_ubid_empty_dataframe(self):
        """Test adding UBID to an empty GeoDataFrame"""
        # Create empty GeoDataFrame
        gdf = gpd.GeoDataFrame({"id": [], "geometry": []}, crs="EPSG:4326")

        # Add UBID
        result_gdf = add_ubid_to_geodataframe(gdf)

        # Check that it handles empty data gracefully
        assert "ubid" in result_gdf.columns
        assert len(result_gdf) == 0

    def test_round_trip_encode_decode(self):
        """Test that encoding then decoding gives reasonable results"""
        # Create test polygon
        coords = [(-105, 39), (-104, 39), (-104, 40), (-105, 40), (-105, 39)]
        original_polygon = Polygon(coords)

        # Encode to UBID
        ubid = encode_ubid(original_polygon)

        # Decode back to bounding box
        decoded_bbox = bounding_box(ubid)

        # The decoded bounding box should overlap with original
        assert original_polygon.intersects(decoded_bbox)

        # Centroid should be roughly in the right place
        decoded_centroid = centroid(ubid)
        original_centroid = original_polygon.centroid

        # Should be reasonably close (within 0.1 degrees)
        assert abs(decoded_centroid.x - original_centroid.x) < 0.1
        assert abs(decoded_centroid.y - original_centroid.y) < 0.1
