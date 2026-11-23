"""
azure_prices.py
Downloads Azure retail prices (in GBP) from the Azure Retail Prices API
for UK South and UK West, for Virtual Machines, Storage and SQL Database.
Saves the raw price rows into the Bronze layer. No cleaning here.
"""

import json                                # save the data as a .json file
import time                                # pause the script for a few seconds
from datetime import datetime, timezone    # date/time stamps, always in UTC
from pathlib import Path                   # build folder paths safely

import requests                            # call the API over the internet

# --- Settings ---
API_URL = "https://prices.azure.com/api/retail/prices"
BRONZE_DIR = Path("data/bronze/azure_prices")

# My choice (Option B): 2 UK regions x 3 services
REGIONS = ["uksouth", "ukwest"]                               # London, Cardiff
SERVICES = ["Virtual Machines", "Storage", "SQL Database"]

def fetch_prices(region, service):
    """Download ALL pages of prices for one region + one service."""
    # Only pay-as-you-go prices ("Consumption") for this region and service
    query = (
        f"armRegionName eq '{region}' "
        f"and serviceName eq '{service}' "
        f"and priceType eq 'Consumption'"
    )
    url = API_URL
    params = {"currencyCode": "'GBP'", "$filter": query}

    all_items = []   # empty list: we'll add each page's rows into it
    page = 1

    while url:   # keep going as long as there is a page to read
        response = requests.get(url, params=params, timeout=60)

        # 429 = "Too Many Requests", so wait, then try the SAME page again
        if response.status_code == 429:
            print("  Too many requests, waiting 10 seconds...")
            time.sleep(10)
            continue   # jump back to the top of the loop (same url)



        response.raise_for_status()
        data = response.json()

        all_items.extend(data["Items"])   # add this page's rows to our list
        print(f"  {region} | {service} | page {page}: {len(data['Items'])} rows")

        url = data.get("NextPageLink")    # next page link, or None at the end
        params = None                     # the next link already has our filter inside
        page += 1

    return all_items

def save_to_bronze(items):
    """Save all price rows into a dated Bronze folder."""
    now = datetime.now(timezone.utc)

    # One folder per day, e.g. data/bronze/azure_prices/2026-11-20/
    folder = BRONZE_DIR / now.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)

    # Time in the file name, so running twice never overwrites a file
    file_path = folder / f"azure_prices_{now.strftime('%Y%m%dT%H%M%SZ')}.json"

    with open(file_path, "w") as f:
        json.dump(items, f, indent=2)

    print(f"Saved {len(items)} rows to: {file_path}")
    return file_path


# Only runs when you start this file directly
if __name__ == "__main__":
    all_prices = []   # one big basket for all 6 combinations

    for region in REGIONS:           # uksouth, then ukwest
        for service in SERVICES:     # VMs, then Storage, then SQL Database
            items = fetch_prices(region, service)
            all_prices.extend(items)

    print("Total rows (all regions and services):", len(all_prices))
    save_to_bronze(all_prices)

