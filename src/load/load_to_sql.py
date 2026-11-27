"""
load_to_sql.py
Loads the 4 Silver Parquet files into the Gold star schema in Azure SQL.
Order: empty the tables -> load dimensions -> load facts -> check row counts.
Safe to re-run: it deletes old rows first, so we never get duplicates.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from test_connection import get_engine  # reuse our tested connection

SILVER = Path("data/silver")

# Phase 4 decision: Azure region -> carbon region id (exact data centre areas)
AZURE_TO_CARBON = {"uksouth": 13, "ukwest": 7}


def strip_tz(series):
    """SQL DATETIME2 has no timezone. Our times are already UTC, so drop the label."""
    s = pd.to_datetime(series)
    return s.dt.tz_convert(None) if s.dt.tz is not None else s


def read_silver():
    """Read the 4 clean Silver files (the 'washed veg' from the fridge)."""
    bill = pd.read_parquet(SILVER / "harbourline_bill/harbourline_bill.parquet")
    carbon = pd.read_parquet(SILVER / "carbon/carbon_intensity.parquet")
    mix = pd.read_parquet(SILVER / "carbon/generation_mix.parquet")
    prices = pd.read_parquet(SILVER / "prices/azure_prices.parquet")
    return bill, carbon, mix, prices


def empty_tables(conn):
    """Delete old rows. Facts first, dims last (foreign keys protect dims)."""
    for table in ["fact_daily_cost", "fact_carbon_intensity", "fact_generation_mix",
                  "dim_resource", "dim_price", "dim_region", "dim_date"]:
        conn.execute(text(f"DELETE FROM dbo.{table};"))
    # restart auto-numbering at 1 so keys stay tidy on every re-run
    for table in ["dim_resource", "dim_price", "fact_daily_cost"]:
        conn.execute(text(f"DBCC CHECKIDENT ('dbo.{table}', RESEED, 0);"))


def build_dim_date(bill, carbon):
    """One row per day seen in the bill or the carbon data."""
    days = pd.concat([
        pd.to_datetime(bill["x_ChargeDate"]),
        strip_tz(carbon["period_start_utc"]).dt.normalize(),
    ]).drop_duplicates().sort_values()
    return pd.DataFrame({
        "date_key": days.dt.strftime("%Y%m%d").astype(int),
        "full_date": days.dt.date,
        "day_of_month": days.dt.day,
        "day_name": days.dt.day_name(),
        "is_weekend": (days.dt.day_of_week >= 5).astype(int),  # 5=Sat, 6=Sun
        "month_num": days.dt.month,
        "month_name": days.dt.month_name(),
        "year_num": days.dt.year,
    })


def build_dim_region(carbon):
    """18 carbon regions; blank azure_region becomes NULL."""
    reg = carbon[["region_id", "region_name", "azure_region"]].drop_duplicates("region_id")
    reg["azure_region"] = reg["azure_region"].replace("", None)
    return reg.sort_values("region_id")


def build_dim_price(prices):
    """Price list, renamed to match the SQL table."""
    p = prices.rename(columns={"region": "azure_region"}).copy()
    p["effective_start"] = strip_tz(p["effective_start"]).dt.date
    return p[["service", "sku", "azure_region", "unit", "price_gbp", "effective_start"]]


def build_dim_resource(bill):
    """One row per VM / disk / database (a resource appears on many days)."""
    res = bill.drop_duplicates("ResourceId")
    return pd.DataFrame({
        "resource_id": res["ResourceId"],
        "resource_name": res["ResourceName"],
        "resource_type": res["ResourceType"],
        "service_name": res["ServiceName"],
        "sku": res["SkuId"],
        "environment": res["x_Environment"],
        "team": res["x_Team"],
        "region_id": res["RegionId"].map(AZURE_TO_CARBON),
    })


def build_fact_cost(bill, conn):
    """Daily cost rows. Swap ResourceId text for the small resource_key number."""
    keys = pd.read_sql("SELECT resource_key, resource_id FROM dbo.dim_resource", conn)
    f = bill.merge(keys, left_on="ResourceId", right_on="resource_id", how="left")
    return pd.DataFrame({
        "date_key": pd.to_datetime(f["x_ChargeDate"]).dt.strftime("%Y%m%d").astype(int),
        "resource_key": f["resource_key"],
        "consumed_quantity": f["ConsumedQuantity"],
        "consumed_unit": f["ConsumedUnit"],
        "billed_cost_gbp": f["BilledCost"],
        "effective_cost_gbp": f["EffectiveCost"],
        "avg_cpu_percent": f["x_AvgCpuPercent"],   # NaN -> NULL for disks
    })


def build_fact_carbon(carbon):
    c = carbon.copy()
    c["period_start_utc"] = strip_tz(c["period_start_utc"])
    c["period_end_utc"] = strip_tz(c["period_end_utc"])
    return c[["period_start_utc", "period_end_utc", "region_id",
              "intensity_g_per_kwh", "intensity_index"]]


def build_fact_mix(mix):
    m = mix.rename(columns={"percent": "percent_share"}).copy()
    m["period_start_utc"] = strip_tz(m["period_start_utc"])
    return m[["period_start_utc", "region_id", "fuel", "percent_share"]]


def load(df, table, conn):
    """Append a DataFrame into an existing SQL table (we built tables in 01_create_tables.sql)."""
    df.to_sql(table, conn, schema="dbo", if_exists="append", index=False, chunksize=1000)
    print(f"  ⬆️  {table:<22} {len(df):>6,} rows")


def check_and_log(conn, expected):
    """Compare SQL row counts with what we sent, and write results to dq_log."""
    print("\n🔎 Checks:")
    for table, exp in expected.items():
        actual = conn.execute(text(f"SELECT COUNT(*) FROM dbo.{table}")).scalar()
        passed = int(actual == exp)
        print(f"  {'✅' if passed else '❌'} {table:<22} expected {exp:>6,}  got {actual:>6,}")
        conn.execute(
            text("INSERT INTO dbo.dq_log (table_name, check_name, expected, actual, passed) "
                 "VALUES (:t, 'row_count_vs_silver', :e, :a, :p)"),
            {"t": table, "e": str(exp), "a": str(actual), "p": passed},
        )
    total = conn.execute(text("SELECT SUM(billed_cost_gbp) FROM dbo.fact_daily_cost")).scalar()
    print(f"  💷 Total billed cost in SQL: £{total:,.2f}  (Silver: £39,985.10)")


if __name__ == "__main__":
    bill, carbon, mix, prices = read_silver()
    engine = get_engine()

    # engine.begin() = one transaction: if anything fails, NOTHING is half-loaded
    with engine.begin() as conn:
        print("🧹 Emptying tables...")
        empty_tables(conn)

        print("📥 Loading dimensions...")
        d_date = build_dim_date(bill, carbon);  load(d_date, "dim_date", conn)
        d_region = build_dim_region(carbon);    load(d_region, "dim_region", conn)
        d_price = build_dim_price(prices);      load(d_price, "dim_price", conn)
        d_res = build_dim_resource(bill);       load(d_res, "dim_resource", conn)

        print("📥 Loading facts...")
        f_cost = build_fact_cost(bill, conn);   load(f_cost, "fact_daily_cost", conn)
        f_carbon = build_fact_carbon(carbon);   load(f_carbon, "fact_carbon_intensity", conn)
        f_mix = build_fact_mix(mix);            load(f_mix, "fact_generation_mix", conn)

        check_and_log(conn, {
            "dim_date": len(d_date), "dim_region": len(d_region),
            "dim_price": len(d_price), "dim_resource": len(d_res),
            "fact_daily_cost": len(f_cost), "fact_carbon_intensity": len(f_carbon),
            "fact_generation_mix": len(f_mix),
        })
    print("\n🎉 Gold layer loaded into Azure SQL.") 