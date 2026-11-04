#!/usr/bin/env python3
"""
Export dbt marts from the local DuckDB warehouse to tableau/data/*.csv for Tableau Public
(which cannot connect to DuckDB or a private Azure SQL database).

Every file is checked against a 5 MB limit so the extracts stay small enough to commit.
Customer PII columns are never exported.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("DBT_DUCKDB_PATH", ROOT / "data" / "warehouse" / "kenya_retail.duckdb"))
OUT = ROOT / "tableau" / "data"
MAX_BYTES = 5 * 1024 * 1024

EXPORTS = {
    "monthly_revenue": "select * from marts.mart_monthly_revenue order by order_month",
    "cohort_retention": "select * from marts.mart_cohort_retention order by cohort_month, months_since_first_order",
    "channel_performance": "select * from marts.mart_channel_performance order by month, channel",
    "customer_rfm": "select * from marts.mart_customer_rfm order by customer_id",
    "sales_by_county": "select * from marts.mart_sales_by_county order by order_month, county_name, channel, category",
    "products": "select * from marts.dim_products order by product_id",
    # customer dimension WITHOUT name / email / phone
    "customers": """
        select customer_id, county_name, region, signup_date, signup_channel, acquisition_channel,
               first_order_date, last_order_date, cohort_month, days_to_first_order,
               lifetime_orders, round(lifetime_net_revenue, 2) as lifetime_net_revenue,
               round(avg_order_value, 2) as avg_order_value, lifecycle_status
        from marts.dim_customers order by customer_id""",
}


def main() -> int:
    if not DB.exists():
        print(f"Warehouse not found at {DB}. Run `make build` first.", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    too_big = []
    for name, sql in EXPORTS.items():
        df = con.sql(sql).df()
        path = OUT / f"{name}.csv"
        df.to_csv(path, index=False, float_format="%.4f")
        size = path.stat().st_size
        flag = "  <-- over 5 MB!" if size > MAX_BYTES else ""
        print(f"  {name:<20} {len(df):>8,} rows  {size / 1024:>8.0f} KB -> {path.relative_to(ROOT)}{flag}")
        if size > MAX_BYTES:
            too_big.append(name)
    con.close()
    if too_big:
        print(f"ERROR: {too_big} exceed 5 MB", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
