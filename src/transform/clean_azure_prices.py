"""
clean_azure_prices.py
Phase 4 (Silver): turn the big Azure price list (16k rows) into a small,
clean price table with ONE price per (service, sku, region).
"""

# --- Toolbox ---
import glob
import json
from pathlib import Path
import pandas as pd

BRONZE_PATTERN = "data/bronze/**/*price*.json"
SILVER_DIR = Path("data/silver/prices")

# The 4 VM sizes Harbourline uses (from the generator)
VM_SIZES = ["Standard_D2s_v5", "Standard_D4s_v5", "Standard_D8s_v5", "Standard_D16s_v5"]
SQL_PRODUCT = "SQL Database Single/Elastic Pool General Purpose - Compute Gen5"


def find_latest_bronze_file(pattern):
    """Return the newest Bronze file that matches the pattern."""
    files = glob.glob(pattern, recursive=True)
    if not files:
        raise FileNotFoundError(f"No Bronze file found for: {pattern}")
    return sorted(files)[-1]


def load_prices(path):
    """Read the JSON list of price rows into a table."""
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    return pd.DataFrame(rows)


def pick_vm_prices(df):
    """Linux, pay-as-you-go, hourly prices for our 4 VM sizes."""
    mask = (
        (df["serviceName"] == "Virtual Machines")
        & (df["armSkuName"].isin(VM_SIZES))
        & (~df["productName"].str.contains("Windows"))      # Linux only
        & (~df["skuName"].str.contains("Spot|Low Priority"))  # normal VMs, not cheap 'can be stopped' ones
        & (df["unitOfMeasure"] == "1 Hour")
    )
    out = df[mask].copy()
    out["service"] = "vm"
    out["sku"] = out["armSkuName"]
    return out


def pick_disk_prices(df):
    """The P10 premium SSD disk we attach to every VM."""
    mask = (df["serviceName"] == "Storage") & (df["meterName"] == "P10 LRS Disk")
    out = df[mask].copy()
    out["service"] = "disk"
    out["sku"] = "P10 LRS"
    return out


def pick_sql_prices(df):
    """SQL Database General Purpose Gen5, normal (not zone-redundant)."""
    mask = (
        (df["productName"] == SQL_PRODUCT)
        & (df["meterName"] == "vCore")
        & (~df["skuName"].str.contains("Zone"))
    )
    out = df[mask].copy()
    out["service"] = "sql"
    out["sku"] = out["skuName"]          # e.g. "8 vCore"
    return out


def build_price_table(df):
    """Stack the 3 lists, tidy the columns, keep ONE price per (service, sku, region)."""
    prices = pd.concat([pick_vm_prices(df), pick_disk_prices(df), pick_sql_prices(df)])

    prices = prices.rename(columns={
        "armRegionName": "region",
        "retailPrice": "price_gbp",
        "unitOfMeasure": "unit",
        "effectiveStartDate": "effective_start",
    })
    prices["effective_start"] = pd.to_datetime(prices["effective_start"], utc=True)

    # Same item can appear more than once (older/newer price) -> keep the newest
    prices = prices.sort_values("effective_start")
    prices = prices.drop_duplicates(subset=["service", "sku", "region"], keep="last")

    keep = ["service", "sku", "region", "unit", "price_gbp", "effective_start"]
    return prices[keep].sort_values(["service", "sku", "region"]).reset_index(drop=True)


def check_quality(prices):
    """Health check + a useful comparison: how much dearer is UK West?"""
    print("\n🩺 Quality checks")
    print("Rows per service:")
    print(prices["service"].value_counts())
    print("Blanks:", prices.isna().sum().sum())
    print("Duplicates:", prices.duplicated(subset=["service", "sku", "region"]).sum())

    vms = prices[prices["service"] == "vm"].pivot(index="sku", columns="region", values="price_gbp")
    vms["ukwest_vs_uksouth_%"] = ((vms["ukwest"] / vms["uksouth"] - 1) * 100).round(1)
    print("\nVM prices (£/hour) by region:")
    print(vms)


def save_to_silver(prices):
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    file_path = SILVER_DIR / "azure_prices.parquet"
    prices.to_parquet(file_path, index=False)
    print(f"\n💾 Saved {len(prices)} rows to: {file_path}")


# --- Run ---
if __name__ == "__main__":
    path = find_latest_bronze_file(BRONZE_PATTERN)
    print("📂 Reading:", path)
    raw = load_prices(path)
    print("Bronze rows:", len(raw))

    prices = build_price_table(raw)
    check_quality(prices)
    save_to_silver(prices)

    print("\nDisk + a few SQL rows:")
    print(prices[prices["service"] != "vm"].head(8))