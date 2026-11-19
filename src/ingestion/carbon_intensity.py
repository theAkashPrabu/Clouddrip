"""
carbon_intensity.py
Downloads UK grid carbon intensity (by region) from the National Grid
Carbon Intensity API and saves the raw JSON into the Bronze layer.
Bronze rule: save the data exactly as received. No cleaning here.
"""

import json                                # save the data as a .json file
from datetime import datetime, timezone    # date/time stamps, always in UTC
from pathlib import Path                   # build folder paths safely

import requests                            # call the API over the internet

# --- Settings ---
# pt24h = "the past 24 hours" up to the time we give it
API_URL = "https://api.carbonintensity.org.uk/regional/intensity/{end}/pt24h"
BRONZE_DIR = Path("data/bronze/carbon_intensity")

def fetch_carbon_intensity():
    """Call the API for the past 24 hours and return the raw JSON."""
    # Current time in UTC, in the format the API wants, e.g. 2026-11-19T08:30Z
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    url = API_URL.format(end=end)  # put the time into the {end} placeholder

    print(f"Calling: {url}")
    response = requests.get(url, timeout=30)  # give up after 30 seconds
    response.raise_for_status()               # stop with a clear error if the call failed

    return response.json()                    # turn the reply text into Python data


def save_to_bronze(data):
    """Save the raw JSON into a dated Bronze folder."""
    now = datetime.now(timezone.utc)

    # One folder per day, e.g. data/bronze/carbon_intensity/2026-11-19/
    folder = BRONZE_DIR / now.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)  # create the folder if it's missing

    # Time in the file name, so running twice never overwrites a file
    file_path = folder / f"carbon_intensity_{now.strftime('%Y%m%dT%H%M%SZ')}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)  # write what the API sent, unchanged

    print(f"Saved: {file_path}")
    return file_path

# Only runs when you start this file directly (not when another file imports it)
if __name__ == "__main__":
    data = fetch_carbon_intensity()
    print("Time periods received:", len(data["data"]))
    save_to_bronze(data)