# !/usr/bin/env python
"""
SEED Platform (TM), Copyright (c) Alliance for Sustainable Energy, LLC, and other contributors.
See also https://github.com/SEED-platform/cbl-workflow/blob/main/LICENSE.md
"""

import gzip
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any

import geopandas as gpd
import mercantile
import pandas as pd
from dotenv import load_dotenv
from shapely.geometry import Point

from building_data_utilities.common import Location
from building_data_utilities.geocode_addresses import geocode_addresses
from building_data_utilities.normalize_address import normalize_address
from building_data_utilities.ubid import bounding_box, centroid, encode_ubid
from building_data_utilities.update_dataset_links import update_dataset_links
from building_data_utilities.update_quadkeys import update_quadkeys

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()


def main():
    AMAZON_API_KEY = os.getenv("AMAZON_API_KEY")
    if not AMAZON_API_KEY:
        sys.exit("Missing Amazon Location Services API key")

    AMAZON_BASE_URL = os.getenv("AMAZON_BASE_URL", "https://places.geo.us-east-2.api.aws/v2")
    AMAZON_APP_ID = os.getenv("AMAZON_APP_ID", None)

    if not os.path.exists("locations.json"):
        sys.exit("Missing locations.json file")

    quadkey_path = Path("data/quadkeys")
    if not quadkey_path.exists():
        quadkey_path.mkdir(parents=True, exist_ok=True)

    with open("locations.json") as f:
        locations: list[Location] = json.load(f)

    for loc in locations:
        loc["street"] = normalize_address(loc["street"])

    data = geocode_addresses(locations, AMAZON_API_KEY, AMAZON_BASE_URL, AMAZON_APP_ID)

    # TODO confirm high quality geocoding results, and that all results have latitude/longitude properties

    # Find all quadkeys that the coordinates fall within
    quadkeys = set()
    for datum in data:
        tile = mercantile.tile(datum["longitude"], datum["latitude"], 9)
        quadkey = int(mercantile.quadkey(tile))
        quadkeys.add(quadkey)
        datum["quadkey"] = quadkey

    # Download quadkey dataset links
    update_dataset_links()

    # Download quadkeys
    update_quadkeys(list(quadkeys))

    # Loop properties and load quadkeys as necessary
    loaded_quadkeys: dict[int, Any] = {}
    for datum in data:
        quadkey = datum["quadkey"]
        if quadkey not in loaded_quadkeys:
            print(f"Loading {quadkey}")

            with gzip.open(f"data/quadkeys/{quadkey}.geojsonl.gz", "rb") as f:
                loaded_quadkeys[quadkey] = gpd.read_file(f)
                print(f"  {len(loaded_quadkeys[quadkey])} footprints in quadkey")

        geojson = loaded_quadkeys[quadkey]
        point = Point(datum["longitude"], datum["latitude"])
        point_gdf = gpd.GeoDataFrame(crs="epsg:4326", geometry=[point])

        # intersections have `geometry`, `index_right`, and `height`
        intersections = gpd.sjoin(point_gdf, geojson)
        if len(intersections) >= 1:
            footprint = geojson.iloc[intersections.iloc[0].index_right]
            datum["footprint_match"] = "intersection"
        else:
            footprint = geojson.iloc[geojson.distance(point).sort_values().index[0]]
            datum["footprint_match"] = "closest"
        datum["geometry"] = footprint.geometry
        datum["height"] = footprint.height if footprint.height != -1 else None

        # Determine UBIDs from footprints
        datum["ubid"] = encode_ubid(datum["geometry"])

    # Save covered building list as csv and GeoJSON
    columns = [
        "address", "city", "state", "postal_code", "side_of_street", "neighborhood", "county",
        "country", "latitude", "longitude", "quality", "footprint_match", "height", "ubid",
        "geometry"]  # fmt: off
    gdf = gpd.GeoDataFrame(data=data, columns=columns)
    gdf.to_csv("data/covered-buildings.csv", index=False)
    gdf.to_file("data/covered-buildings.geojson", driver="GeoJSON")

    # Save a custom GeoJSON with 3 layers: UBID bounding boxes, footprints, then UBID centroids
    bounding_boxes = gpd.GeoDataFrame(
        data=[{"UBID Bounding Box": datum["address"], "geometry": bounding_box(datum["ubid"])} for datum in data],
        columns=["UBID Bounding Box", "geometry"],
    )
    centroids = gpd.GeoDataFrame(
        data=[{"UBID Centroid": datum["address"], "geometry": centroid(datum["ubid"])} for datum in data],
        columns=["UBID Centroid", "geometry"],
    )
    gdf_ubid = pd.concat([bounding_boxes, gdf, centroids])
    with open("data/covered-buildings-ubid.geojson", "w") as f:
        f.write(gdf_ubid.to_json(drop_id=True, na="drop"))


if __name__ == "__main__":
    main()
