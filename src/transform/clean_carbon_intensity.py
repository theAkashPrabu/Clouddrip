"""
clean_carbon_intensity.py
Phase 4 (Silver): flatten the nested carbon intensity JSON from Bronze.
"""

# --- Toolbox ---
import glob
import json
from pathlib import Path
import pandas as pd

BRONZE_PATTERN = "data/bronze/**/*carbon*.json"
SILVER_DIR = Path("data/silver/carbon")
# Akash's Decision 2: match each Azure data centre to its exact carbon region
REGION_TO_AZURE = {
    13: "uksouth",      # London
    7: "ukwest",      # South Wales (Cardiff)
}


def find_latest_bronze_file(pattern):
    """Return the newest Bronze file that matches the pattern."""
    files = glob.glob(pattern, recursive=True)
    if not files:
        raise FileNotFoundError(f"No Bronze file found for: {pattern}")
    return sorted(files)[-1]


def flatten_intensity(periods):
    """Unpack the boxes: one row per (half-hour, region)."""
    df = pd.json_normalize(
        periods,
        record_path="regions",   # go inside each half-hour's list of regions
        meta=["from", "to"],     # copy the half-hour's times onto every region row
    )
    # Rename to clear snake_case names (nested keys come out like "intensity.forecast")
    df = df.rename(columns={
        "from": "period_start_utc",
        "to": "period_end_utc",
        "regionid": "region_id",
        "shortname": "region_name",
        "intensity.forecast": "intensity_g_per_kwh",
        "intensity.index": "intensity_index",
    })
    # Text -> real dates (same trick as the bill)
    df["period_start_utc"] = pd.to_datetime(df["period_start_utc"], utc=True)
    df["period_end_utc"] = pd.to_datetime(df["period_end_utc"], utc=True)
    # Tag the 2 regions that have our Azure data centres (others stay blank)
    df["azure_region"] = df["region_id"].map(REGION_TO_AZURE)

    keep = ["period_start_utc", "period_end_utc", "region_id", "region_name",
            "intensity_g_per_kwh", "intensity_index", "azure_region"]
    return df[keep]


def load_json(path):
    """Read the raw JSON file into Python (lists + dictionaries)."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    # The API wraps everything in {"data": [...]} - unwrap it if it's there
    if isinstance(raw, dict) and "data" in raw:
        raw = raw["data"]
    return raw
def flatten_generation_mix(periods):
    """Decision 3: second small table - one row per (half-hour, region, fuel)."""
    df = pd.json_normalize(
        periods,
        record_path=["regions", "generationmix"],   # two boxes deep: region -> fuel list
        meta=["from", ["regions", "regionid"]],      # copy time + region id onto each fuel row
    )
    df = df.rename(columns={
        "from": "period_start_utc",
        "regions.regionid": "region_id",
        "perc": "percent",
    })
    df["period_start_utc"] = pd.to_datetime(df["period_start_utc"], utc=True)
    df["region_id"] = df["region_id"].astype(int)
    return df[["period_start_utc", "region_id", "fuel", "percent"]]


def check_quality(intensity, mix):
    """Quick health check before saving."""
    print("\n🩺 Quality checks")
    print("Blanks in intensity (ignoring azure_region):",
          intensity.drop(columns="azure_region").isna().sum().sum())
    dupes = intensity.duplicated(subset=["period_start_utc", "region_id"]).sum()
    print("Duplicate half-hour + region rows:", dupes)
    print("Intensity range (g/kWh):", intensity["intensity_g_per_kwh"].min(),
          "to", intensity["intensity_g_per_kwh"].max())
    # Fuel percentages should add up to about 100 for each half-hour + region
    totals = mix.groupby(["period_start_utc", "region_id"])["percent"].sum()
    print("Mix totals (should be ~100):", round(totals.min(), 1), "to", round(totals.max(), 1))


def save_to_silver(intensity, mix):
    """Save both clean tables as Parquet (overwrite = latest clean copy)."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    intensity.to_parquet(SILVER_DIR / "carbon_intensity.parquet", index=False)
    mix.to_parquet(SILVER_DIR / "generation_mix.parquet", index=False)
    print(f"\n💾 Saved {len(intensity)} intensity rows and {len(mix)} mix rows to: {SILVER_DIR}")


# --- Test block ---
if __name__ == "__main__":
    path = find_latest_bronze_file(BRONZE_PATTERN)
    print("📂 Reading:", path)
    periods = load_json(path)

    intensity = flatten_intensity(periods)
    mix = flatten_generation_mix(periods)
    print("Intensity shape:", intensity.shape)
    print("Mix shape:", mix.shape)

    check_quality(intensity, mix)
    save_to_silver(intensity, mix)