"""
explore_prices.py
Quick look at the Azure prices in Bronze, to choose realistic VM sizes
for the Harbourline bill. Exploring only: nothing is saved.
"""

import json
from pathlib import Path

import pandas as pd   # "Excel inside Python": tables with rows and columns

# Find the newest prices file in Bronze (names sort by date and time)
files = sorted(Path("data/bronze/azure_prices").glob("*/*.json"))
latest = files[-1]   # [-1] = the last one in the list = the newest
print("Reading:", latest)

with open(latest) as f:
    prices = pd.DataFrame(json.load(f))   # turn the JSON list into a table

print("Rows, columns:", prices.shape)

# Keep only normal Linux, pay-as-you-go VM prices per hour
vms = prices[
    (prices["serviceName"] == "Virtual Machines")
    & (prices["unitOfMeasure"] == "1 Hour")
    & (~prices["productName"].str.contains("Windows"))
    & (~prices["skuName"].str.contains("Spot|Low Priority"))
]

# 4 popular general-purpose sizes: 2, 4, 8 and 16 CPUs
sizes = ["Standard_D2s_v5", "Standard_D4s_v5", "Standard_D8s_v5", "Standard_D16s_v5"]
table = vms[vms["armSkuName"].isin(sizes)]

print(table[["armRegionName", "armSkuName", "retailPrice"]]
      .sort_values(["armSkuName", "armRegionName"])
      .to_string(index=False))

# --- Storage: Premium SSD managed disks in UK South (price per disk per month) ---
disks = prices[
    (prices["serviceName"] == "Storage")
    & (prices["armRegionName"] == "uksouth")
    & (prices["productName"].str.contains("Premium SSD Managed Disks"))
]
print("\nManaged disks (UK South):")
print(disks[["skuName", "meterName", "unitOfMeasure", "retailPrice"]]
      .sort_values("skuName").head(15).to_string(index=False))

# --- SQL Database: General Purpose prices per hour in UK South ---
sql = prices[
    (prices["serviceName"] == "SQL Database")
    & (prices["armRegionName"] == "uksouth")
    & (prices["productName"].str.contains("General Purpose"))
    & (prices["unitOfMeasure"] == "1 Hour")
]
print("\nSQL Database General Purpose (UK South):")
print(sql[["productName", "skuName", "meterName", "retailPrice"]]
      .head(15).to_string(index=False))