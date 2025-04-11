# CBL Workflow

> Covered Building List Workflow

Given a list of addresses, this workflow will automatically:

- Normalize each address
- Geocode each address via MapQuest to a lat/long coordinate
- Download the [Microsoft Building Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints/) for all areas encompassed by the geocoded coordinates
- Find the footprint that intersects (or is closest to) each geocoded coordinate
- Generate the UBID for each footprint
- Export the resulting data as csv and GeoJSON

### Prerequisites

1. Optionally create a Virtualenv Environment
2. Dependencies are managed through Poetry, install with `pip install poetry`
3. Install dependencies with `poetry install`
4. Create a `.env` file in the root with your MapQuest API key in the format:

   ```dotenv
   MAPQUEST_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

   Note that if an env key for MAPQUEST_API_KEY exists in your profile, then it use that over the .env file.

5. Create a `locations.json` file in the root containing a list of addresses to process in the format:

   ```json
   [
     {
       "street": "100 W 14th Ave Pkwy",
       "city": "Denver",
       "state": "CO"
     },
     {
       "street": "200 E Colfax Ave",
       "city": "Denver",
       "state": "CO"
     },
     {
       "street": "320 W Colfax Ave",
       "city": "Denver",
       "state": "CO"
     }
   ]
   ```

### Running the Workflow

1. Run the workflow with `python main.py` or `poetry run python main.py`
2. The results will be saved to `./data/covered-buildings.csv` and `./data/covered-buildings.geojson`. Example of these files are in the `tests/data` directory as well.

### Notes

- This workflow is optimized to be self-updating, and only downloads quadkeys and quadkey dataset-links if they haven't previously been downloaded or if an update is available
- Possible next steps:
  - Cache geocoding results (if allowed) to avoid API limit penalties when re-running
  - Allow other geocoders like Google, without persisting the geocoding results
  - Add distance from geocoded result to footprint boundary, `proximity_to_geocoding_coord` (intersections would be 0)
  - Update [SEEDling](https://github.com/SEED-platform/seedling) to include this workflow, allowing you to upload an address list file and progressively update the map with records as they're processed (with a filterable sidebar containing list of results), and allowing you to fix which footprint is selected for a specific property

### Disclaimer

When using this tool with the MapQuest geocoding API (or any other geocoder) always confirm that the terms of service allow for using and storing geocoding results (as with the MapQuest Enterprise license)
