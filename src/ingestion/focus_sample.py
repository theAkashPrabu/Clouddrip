"""
focus_sample.py
Downloads the public FOCUS 1.0 sample billing data (10,000 rows, CSV)
from the FinOps Foundation's GitHub and saves it into Bronze unchanged.
Licence: CC BY 4.0 (FinOps Foundation). Used to learn the real FOCUS columns.
"""

from datetime import datetime, timezone    # date/time stamps, always in UTC
from pathlib import Path                   # build folder paths safely

import requests                            # download the file

# --- Settings ---
SOURCE_URL = (
    "https://raw.githubusercontent.com/FinOps-Open-Cost-and-Usage-Spec/"
    "FOCUS-Sample-Data/main/FOCUS-1.0/focus_sample_10000.csv"
)
BRONZE_DIR = Path("data/bronze/focus_sample")


def download_focus_sample():
    """Download the CSV file and return its raw bytes."""
    print(f"Downloading: {SOURCE_URL}")
    response = requests.get(SOURCE_URL, timeout=60)
    response.raise_for_status()
    return response.content      # raw bytes, exactly as GitHub sent them


def save_to_bronze(content):
    """Save the raw CSV into a dated Bronze folder."""
    now = datetime.now(timezone.utc)

    # ✍️ YOUR TURN: write these 2 lines yourself
    # Line 1: make 'folder' = BRONZE_DIR + today's date (YYYY-MM-DD)
    # Line 2: create that folder if it doesn't exist


    folder = BRONZE_DIR / now.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"focus_sample_10000_{now.strftime('%Y%m%dT%H%M%SZ')}.csv"

    with open(file_path, "wb") as f:   # "wb" = write bytes, an exact copy
        f.write(content)

    print(f"Saved {len(content) / 1_000_000:.1f} MB to: {file_path}")
    return file_path


if __name__ == "__main__":
    content = download_focus_sample()
    save_to_bronze(content)