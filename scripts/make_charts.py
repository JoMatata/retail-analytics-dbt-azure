#!/usr/bin/env python3
"""
Render PREVIEW charts (Python / matplotlib) from the dbt marts into docs/images/.

These are quick previews for the README. The interactive deliverable is the Tableau Public
dashboard specified in tableau/DASHBOARD_SPEC.md.
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("DBT_DUCKDB_PATH", ROOT / "data" / "warehouse" / "kenya_retail.duckdb"))
OUT = ROOT / "docs" / "images"

# Fixed categorical order (colour follows the entity, never its rank)
CHANNEL_COLORS = {"web": "#2a78d6", "app": "#eb6834", "store": "#1baf7a"}
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
SUBTITLE = "Preview chart (Python) - synthetic data"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 150,
})


def title(ax, main: str, sub: str = SUBTITLE):
    ax.set_title(f"{main}\n", loc="left", fontsize=13, fontweight="bold", color=INK)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9, color=INK_2)


def kes_millions(x, _):
    return f"KES {x / 1e6:,.0f}M"


def monthly_revenue(con):
    df = con.sql("select order_month, net_revenue, new_customer_revenue, returning_customer_revenue "
                 "from marts.mart_monthly_revenue order by order_month").df()
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = df["order_month"]
    ax.bar(x, df["returning_customer_revenue"], width=24, color="#2a78d6", label="Returning customers")
    ax.bar(x, df["new_customer_revenue"], width=24, bottom=df["returning_customer_revenue"],
           color="#eb6834", label="New customers", edgecolor="white", linewidth=1)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(kes_millions))
    peak = df.loc[df["net_revenue"].idxmax()]
    ax.annotate(f"Dec-25 peak\nKES {peak.net_revenue / 1e6:,.1f}M", (peak.order_month, peak.net_revenue),
                xytext=(-95, -10), textcoords="offset points", fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.8))
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="x", visible=False)
    title(ax, "Monthly net revenue: new vs returning customers")
    fig.tight_layout()
    fig.savefig(OUT / "monthly_revenue.png")
    plt.close(fig)


def cohort_heatmap(con):
    df = con.sql("select cohort_month, months_since_first_order m, retention_rate "
                 "from marts.mart_cohort_retention where months_since_first_order <= 12").df()
    pv = df.pivot(index="cohort_month", columns="m", values="retention_rate").sort_index()
    fig, ax = plt.subplots(figsize=(10, 7.5))
    im = ax.imshow(pv.values, cmap="Blues", vmin=0, vmax=0.6, aspect="auto")
    ax.set_xticks(range(pv.shape[1]), [str(c) for c in pv.columns])
    ax.set_yticks(range(pv.shape[0]), [d.strftime("%b %Y") for d in pv.index])
    ax.set_xlabel("Months since first order")
    ax.grid(False)
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]):
            v = pv.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=7,
                        color="white" if v > 0.35 else INK, fontweight="bold" if j == 0 else "normal")
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, format=mtick.PercentFormatter(1.0))
    cb.outline.set_visible(False)
    title(ax, "Monthly cohort retention (share of cohort ordering again)",
          SUBTITLE + " - month 0 = 100% by definition")
    fig.tight_layout()
    fig.savefig(OUT / "cohort_retention.png")
    plt.close(fig)


def channel_economics(con):
    df = con.sql("""
        select channel, sum(marketing_spend) / sum(new_customers) as cac,
               sum(net_revenue) / sum(marketing_spend) as roas,
               sum(first_order_revenue) / sum(marketing_spend) as fo_roas
        from marts.mart_channel_performance group by channel""").df().set_index("channel").loc[["web", "app", "store"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    colors = [CHANNEL_COLORS[c] for c in df.index]
    b = a1.bar(df.index, df["cac"], color=colors, width=0.55)
    a1.bar_label(b, labels=[f"KES {v:,.0f}" for v in df["cac"]], padding=3, color=INK, fontsize=9)
    a1.set_ylabel("KES per new customer")
    a1.grid(axis="x", visible=False)
    title(a1, "Customer acquisition cost (CAC)", "Spend / new customers, 2024-25")
    b = a2.bar(df.index, df["roas"], color=colors, width=0.55)
    a2.bar_label(b, labels=[f"{v:.1f}x" for v in df["roas"]], padding=3, color=INK, fontsize=9)
    a2.set_ylabel("Net revenue / spend")
    a2.grid(axis="x", visible=False)
    title(a2, "Return on ad spend (ROAS)", "All channel revenue / spend, 2024-25")
    fig.text(0.01, 0.01, SUBTITLE, fontsize=8, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "channel_cac_roas.png")
    plt.close(fig)


def rfm_segments(con):
    df = con.sql("""select rfm_segment, count(*) customers, sum(monetary) revenue
                    from marts.mart_customer_rfm group by 1 order by revenue""").df()
    df["rev_share"] = df["revenue"] / df["revenue"].sum()
    df["cust_share"] = df["customers"] / df["customers"].sum()
    fig, ax = plt.subplots(figsize=(10, 4.6))
    y = np.arange(len(df))
    ax.barh(y + 0.2, df["cust_share"], height=0.38, color="#2a78d6", label="Share of customers")
    ax.barh(y - 0.2, df["rev_share"], height=0.38, color="#eb6834", label="Share of revenue")
    ax.set_yticks(y, df["rfm_segment"])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    for yi, v in zip(y, df["rev_share"]):
        ax.text(v + 0.005, yi - 0.2, f"{v:.0%}", va="center", fontsize=8, color=INK)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="y", visible=False)
    title(ax, "RFM segments: share of customers vs share of revenue")
    fig.tight_layout()
    fig.savefig(OUT / "rfm_segments.png")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    for fn in (monthly_revenue, cohort_heatmap, channel_economics, rfm_segments):
        fn(con)
        print(f"  wrote {fn.__name__}")
    con.close()


if __name__ == "__main__":
    main()
