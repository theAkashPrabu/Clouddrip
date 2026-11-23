"""
clean_harbourline_bill.py
Phase 4 (Silver): clean the simulated Harbourline bill from Bronze.
Bronze stays untouched - we read it, tidy it, and save a NEW file in data/silver/.
"""

# --- Toolbox: imports at the top ---
import glob          # finds files that match a pattern (like a search box)
import json          # turns JSON text into a Python dictionary
import pandas as pd  # our main data tool
from pathlib import Path   # handy for building folder/file paths

# Where to look: any CSV with "harbourline" in its name, in any folder under data/bronze
BRONZE_PATTERN = "data/bronze/**/*harbourline*.csv"
SILVER_DIR = Path("data/silver/harbourline_bill")


def find_latest_bronze_file(pattern):
    """Return the newest Bronze file that matches the pattern."""
    files = glob.glob(pattern, recursive=True)   # recursive=True means look inside sub-folders too
    if not files:
        raise FileNotFoundError(f"No Bronze file found for: {pattern}")
    # Our folders/file names contain the date + UTC timestamp,
    # so sorting by name puts the newest file LAST
    return sorted(files)[-1]


def load_bill(path):
    """Read the raw CSV exactly as Bronze saved it."""
    return pd.read_csv(path)

DATE_COLUMNS = [
    "BillingPeriodStart",
    "BillingPeriodEnd",
    "ChargePeriodStart",
    "ChargePeriodEnd",
]


def fix_dates(df):
    """Turn date TEXT into real dates (in UTC)."""
    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], utc=True)   # <- replace the blank
    # Handy extra column: just the day (no time) - useful for daily charts later
    df["x_ChargeDate"] = df["ChargePeriodStart"].dt.date
    return df


def split_tags(df):
    """Peel the Tags 'sticker' into two columns: environment and team."""
    tags_dicts = df["Tags"].apply(json.loads)      # each text -> a Python dictionary
    tags_table = pd.json_normalize(tags_dicts)     # list of dictionaries -> a small table
    df["x_Environment"] = tags_table["environment"]
    df["x_Team"] = tags_table["team"]
    return df


def check_quality(df):
    """Quick health check before saving: blanks, duplicates, total cost."""
    print("\n🩺 Quality checks")

    # 1) Blanks: show only columns that have missing values
    nulls = df.isna().sum()
    print("Columns with blanks:")
    print(nulls[nulls > 0])

    # 2) Duplicates: the same resource should appear only once per day
    duplicates = df.duplicated(subset=["ResourceId", "ChargePeriodStart"]).sum()
    print("Duplicate resource-days:", duplicates)

    # 3) Total cost should still match the Bronze bill (£39,985.10)
    print("Total BilledCost (£):", round(df["BilledCost"].sum(), 2))


def save_to_silver(df):
    """Save the clean table as Parquet. Silver = latest clean copy, so we overwrite."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    file_path = SILVER_DIR / "harbourline_bill.parquet"
    df.to_parquet(file_path, index=False)
    print(f"\n💾 Saved {len(df)} rows to: {file_path}")
    return file_path

if __name__ == "__main__":
    path = find_latest_bronze_file(BRONZE_PATTERN)
    print("📂 Reading:", path)
    df = load_bill(path)

    df = fix_dates(df)
    df = split_tags(df)

    check_quality(df)
    save_to_silver(df)

    # Prove Parquet remembers the types: read it back and check
    back = pd.read_parquet(SILVER_DIR / "harbourline_bill.parquet")
    print("\nRead back - ChargePeriodStart type:", back["ChargePeriodStart"].dtype)