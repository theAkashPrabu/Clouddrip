"""
generate_harbourline_bill.py
Creates a SIMULATED one-month Azure bill for the fictional client
Harbourline Insurance, in FOCUS format (same column names as the real
FOCUS sample). Costs use REAL Azure retail prices (GBP) from Bronze.
Hidden waste: idle VMs, oversized VMs, dev/test left on 24/7.
Saved into Bronze as if it was exported from Azure Cost Management.
"""

import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

# --- Settings ---
PRICES_DIR = Path("data/bronze/azure_prices")
BRONZE_DIR = Path("data/bronze/harbourline_bill")

MONTH_START = date(2026, 10, 1)   # October 2026
DAYS = 31
HOURS_PER_MONTH = 730             # Azure's standard month for monthly prices

random.seed(42)                   # same "random" numbers every run = repeatable

REGION_NAMES = {"uksouth": "UK South", "ukwest": "UK West"}
SUBSCRIPTION_ID = "sub-harbourline-prod-001"


# ---------- 1. Real prices from Bronze ----------

def load_prices():
    """Read the newest Azure prices file from Bronze into a table."""
    latest = sorted(PRICES_DIR.glob("*/*.json"))[-1]
    print("Using prices from:", latest)
    with open(latest) as f:
        return pd.DataFrame(json.load(f))


def vm_price(prices, sku, region):
    """£ per hour for a Linux, pay-as-you-go VM."""
    match = prices[
        (prices["serviceName"] == "Virtual Machines")
        & (prices["armSkuName"] == sku)
        & (prices["armRegionName"] == region)
        & (prices["unitOfMeasure"] == "1 Hour")
        & (~prices["productName"].str.contains("Windows"))
        & (~prices["skuName"].str.contains("Spot|Low Priority"))
    ]
    if match.empty:
        raise ValueError(f"No VM price found for {sku} in {region}")
    return match["retailPrice"].min()


def disk_price(prices, disk, region):
    """£ per month for a Premium SSD managed disk, e.g. 'P10'."""
    match = prices[
        (prices["serviceName"] == "Storage")
        & (prices["armRegionName"] == region)
        & (prices["meterName"] == f"{disk} LRS Disk")
    ]
    if match.empty:
        raise ValueError(f"No disk price found for {disk} in {region}")
    return match["retailPrice"].min()


def sql_price(prices, vcores, region):
    """£ per hour for a General Purpose Gen5 SQL database."""
    match = prices[
        (prices["serviceName"] == "SQL Database")
        & (prices["armRegionName"] == region)
        & (prices["productName"] == "SQL Database Single/Elastic Pool General Purpose - Compute Gen5")
        & (prices["skuName"] == f"{vcores} vCore")
        & (prices["meterName"] == "vCore")
    ]
    if match.empty:
        raise ValueError(f"No SQL price found for {vcores} vCore in {region}")
    return match["retailPrice"].min()   # min() also handles duplicate rows


# ---------- 2. Harbourline's resources ----------

# Each line = a group of identical VMs.
# behaviour: "normal", "idle" (waste A), "oversized" (waste B),
#            "dev_always_on" (waste D), "dev_scheduled" (good example)
VM_GROUPS = [
    # name prefix, count, size,               region,    env,    team,        behaviour
    ("hl-web",      30, "Standard_D4s_v5",  "uksouth", "prod", "digital",   "normal"),
    ("hl-app",      25, "Standard_D8s_v5",  "uksouth", "prod", "claims",    "normal"),
    ("hl-batch",    10, "Standard_D16s_v5", "uksouth", "prod", "analytics", "normal"),
    ("hl-dr",       10, "Standard_D8s_v5",  "ukwest",  "prod", "claims",    "normal"),
    ("hl-legacy",    6, "Standard_D8s_v5",  "uksouth", "prod", "claims",    "idle"),
    ("hl-report",    4, "Standard_D16s_v5", "ukwest",  "prod", "finance",   "idle"),
    ("hl-pricing",  10, "Standard_D16s_v5", "uksouth", "prod", "pricing",   "oversized"),
    ("hl-dev",      30, "Standard_D4s_v5",  "uksouth", "dev",  "digital",   "dev_always_on"),
    ("hl-test",      5, "Standard_D4s_v5",  "uksouth", "dev",  "claims",    "dev_scheduled"),
]

SQL_DATABASES = [
    # name,          vCores, region,    env,    team
    ("sql-claims",     16, "uksouth", "prod", "claims"),
    ("sql-policy",     16, "uksouth", "prod", "digital"),
    ("sql-pricing",     8, "uksouth", "prod", "pricing"),
    ("sql-finance",     8, "ukwest",  "prod", "finance"),
    ("sql-customer",    8, "uksouth", "prod", "digital"),
    ("sql-analytics",   8, "uksouth", "prod", "analytics"),
    ("sql-dev",         4, "uksouth", "dev",  "digital"),
    ("sql-test",        4, "uksouth", "dev",  "claims"),
]

# How busy each type of VM is (average CPU % per day: low, high)
CPU_RANGE = {
    "normal": (35, 70),
    "idle": (0.5, 3),
    "oversized": (5, 12),
    "dev_always_on": (3, 15),
    "dev_scheduled": (20, 45),
}


def build_vms():
    """Turn each group into individual VMs, e.g. hl-web-01 ... hl-web-30."""
    vms = []
    for prefix, count, size, region, env, team, behaviour in VM_GROUPS:
        for i in range(1, count + 1):
            vms.append({
                "name": f"{prefix}-{i:02d}",
                "size": size,
                "region": region,
                "env": env,
                "team": team,
                "behaviour": behaviour,
            })
    return vms


# ---------- 3. One bill row per resource per day ----------

def hours_running(behaviour, day):
    """How many hours a VM ran on this day."""
    if behaviour == "dev_scheduled":
        # Good practice: on 08:00-18:00 on weekdays only
        return 10 if day.weekday() < 5 else 0
    return 24   # everything else runs all day, every day (incl. dev_always_on!)


def focus_row(day, name, resource_type, service, category, sku, region,
              quantity, unit, unit_price, env, team, cpu=None):
    """Build one bill row using real FOCUS column names."""
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    cost = round(quantity * unit_price, 6)
    return {
        "BillingAccountId": "ba-harbourline-001",
        "BillingAccountName": "Harbourline Insurance Ltd",
        "BillingCurrency": "GBP",
        "BillingPeriodStart": "2026-10-01T00:00:00Z",
        "BillingPeriodEnd": "2026-11-01T00:00:00Z",
        "ChargePeriodStart": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ChargePeriodEnd": (start + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ChargeCategory": "Usage",
        "ChargeDescription": f"{service} - {sku}",
        "ProviderName": "Microsoft",
        "PublisherName": "Microsoft",
        "InvoiceIssuerName": "Microsoft",
        "RegionId": region,
        "RegionName": REGION_NAMES[region],
        "ResourceId": f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/rg-{team}-{env}/{resource_type}/{name}",
        "ResourceName": name,
        "ResourceType": resource_type,
        "ServiceCategory": category,
        "ServiceName": service,
        "SkuId": sku,
        "SubAccountId": SUBSCRIPTION_ID,
        "SubAccountName": "Harbourline Production",
        "ConsumedQuantity": quantity,
        "ConsumedUnit": unit,
        "PricingQuantity": quantity,
        "PricingUnit": unit,
        "ListUnitPrice": unit_price,
        "ListCost": cost,
        "BilledCost": cost,
        "EffectiveCost": cost,
        "Tags": json.dumps({"environment": env, "team": team}),
        "x_AvgCpuPercent": cpu,   # custom column (FOCUS allows x_ columns)
    }


def generate_rows(prices):
    """Create every bill row for the month."""
    vms = build_vms()
    rows = []

    # Look up each price ONCE (much faster than looking it up for every row)
    vm_prices = {(vm["size"], vm["region"]): vm_price(prices, vm["size"], vm["region"]) for vm in vms}
    disk_prices = {r: disk_price(prices, "P10", r) for r in REGION_NAMES}
    sql_prices = {(v, r): sql_price(prices, v, r) for _, v, r, _, _ in SQL_DATABASES}

    for d in range(DAYS):
        day = MONTH_START + timedelta(days=d)

        # VMs + their OS disk (one P10 disk per VM)
        for vm in vms:
            hours = hours_running(vm["behaviour"], day)
            low, high = CPU_RANGE[vm["behaviour"]]
            cpu = round(random.uniform(low, high), 1) if hours > 0 else None

            if hours > 0:
                rows.append(focus_row(
                    day, vm["name"], "virtualMachines", "Virtual Machines", "Compute",
                    vm["size"], vm["region"], hours, "Hours",
                    vm_prices[(vm["size"], vm["region"])],
                    vm["env"], vm["team"], cpu))

            # Disks are billed every day, even when the VM is switched off
            disk_daily = disk_prices[vm["region"]] * 24 / HOURS_PER_MONTH
            rows.append(focus_row(
                day, f"{vm['name']}-osdisk", "disks", "Storage", "Storage",
                "P10 LRS", vm["region"], 1, "Disk-Days", round(disk_daily, 6),
                vm["env"], vm["team"]))

        # SQL databases run 24/7
        for name, vcores, region, env, team in SQL_DATABASES:
            rows.append(focus_row(
                day, name, "databases", "SQL Database", "Databases",
                f"GP_Gen5_{vcores}", region, 24, "Hours",
                sql_prices[(vcores, region)], env, team,
                round(random.uniform(30, 60), 1)))

    return pd.DataFrame(rows)


   # ---------- 4. Save to Bronze ----------

def save_to_bronze(bill):
    """Save the bill as a CSV in a dated Bronze folder."""
    now = datetime.now(timezone.utc)
    folder = BRONZE_DIR / now.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"harbourline_focus_2026-10_{now.strftime('%Y%m%dT%H%M%SZ')}.csv"
    bill.to_csv(file_path, index=False)
    print(f"Saved {len(bill)} rows to: {file_path}")
    return file_path


if __name__ == "__main__":
    prices = load_prices()
    bill = generate_rows(prices)

    print("\nCost by service (£):")
    print(bill.groupby("ServiceName")["BilledCost"].sum().round(2))
    print("Total for October (£):", round(bill["BilledCost"].sum(), 2))

    save_to_bronze(bill)                                   