"""
check_focus_columns.py
Phase 4.4: does our Silver Harbourline bill follow the real FOCUS standard?
Compare our column names with the real FinOps Foundation FOCUS sample.
"""

import glob
import pandas as pd

# Real FOCUS sample (Bronze) - we only need the header row, so nrows=0
focus_file = sorted(glob.glob("data/bronze/**/*focus_sample*.csv", recursive=True))[-1]
focus_cols = set(pd.read_csv(focus_file, nrows=0).columns)

# Our clean bill (Silver)
our_cols = set(pd.read_parquet("data/silver/harbourline_bill/harbourline_bill.parquet").columns)

print("FOCUS sample columns:", len(focus_cols))
print("Our bill columns:    ", len(our_cols))
print("Shared columns:      ", len(focus_cols & our_cols))   # & = in BOTH sets

extras = sorted(our_cols - focus_cols)                       # - = in ours but NOT in FOCUS
missing = sorted(focus_cols - our_cols)                      # in FOCUS but NOT in ours

print("\n➕ Extra columns in our bill:", extras)
print("➖ FOCUS columns we don't use:", missing)

# The rule: every extra column must be a custom 'x_' column
bad = [c for c in extras if not c.startswith("x_")]
if bad:
    print("\n❌ Not FOCUS-compliant, these extras need an x_ prefix:", bad)
else:
    print("\n✅ FOCUS-compliant: all our extra columns start with x_")