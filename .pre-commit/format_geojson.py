# GeoJSON files do not have a required order to the property elements. THis
# pre-commit script will sort the order of the elements within the GeoJSON
# files
# Author: Nicholas Long (nllong)

# To use, place this file in a .pre-commit file in the root. Add
# the following to the .pre-commit-config.yaml

#   - repo: local
#     hooks:
#       - id: format-geojson-files
#         name: sort the elements in the geojson file
#         entry: python .pre-commit/format_geojson.py
#         language: system
#         files: ^data/source_files/.*\.geojson$


import json
import sys


def sort_keys_custom(key):
    """When sorting, replace underscores with spaces. Also make lowercase, since
    since apparently, that effects the sort order!"""
    return key.replace("_", " ").lower()


def format_geojson(filepath):
    print(f"Formatting GeoJSON {filepath}")
    try:
        with open(filepath, encoding="utf-8") as f:
            geojson_data = json.load(f)

        # Sort the keys in the GeoJSON data
        if "features" in geojson_data:
            for feature in geojson_data["features"]:
                if "properties" in feature:
                    feature["properties"] = dict(
                        sorted(
                            feature["properties"].items(),
                            key=lambda item: sort_keys_custom(item[0]),
                        )
                    )

                    # Move some items to be first -- name, ID, type
                    if "type" in feature["properties"]:
                        feature["properties"] = {
                            "type": feature["properties"]["type"],
                            **feature["properties"],
                        }
                    if "name" in feature["properties"]:
                        feature["properties"] = {
                            "name": feature["properties"]["name"],
                            **feature["properties"],
                        }
                    if "id" in feature["properties"]:
                        feature["properties"] = {
                            "id": feature["properties"]["id"],
                            **feature["properties"],
                        }

        sorted_geojson_data = json.dumps(geojson_data, indent=2)  # , sort_keys=True)

        # Save the formatted GeoJSON data
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(sorted_geojson_data)
            # write out a newline at the end of the file so end-of-file-fixer
            # doesn't complain
            f.write("\n")

    except Exception as e:
        print(f"Failed to format {filepath}: {e}")


if __name__ == "__main__":
    for file in sys.argv[1:]:
        format_geojson(file)
