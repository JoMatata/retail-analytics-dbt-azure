# Tableau Public dashboard — build spec

**Workbook name:** `Kenya Retail Sales Analytics (synthetic data)`
**Status:** to be built in Tableau Public from the CSVs in [`tableau/data/`](data/). Once published, add the
public link and a real screenshot (`docs/images/tableau_dashboard.png`) to the README.

The spec below is written so the workbook can be built click-by-click with no further design decisions.
Every number on the dashboard comes from the dbt marts, so the dashboard and the README always agree.

---

## 1. Data sources

Tableau Public cannot connect to DuckDB or Azure SQL, so connect to the exported text files
(**Connect → Text file**). Use one data source per file, *not* joins, except where noted.

| Data source name | File | Grain | Notes |
|---|---|---|---|
| `Monthly Revenue` | `monthly_revenue.csv` | month | KPIs, trend |
| `Cohorts` | `cohort_retention.csv` | cohort month × months since first order | heatmap |
| `Channels` | `channel_performance.csv` | month × channel | CAC / ROAS |
| `Sales Geo` | `sales_by_county.csv` | month × county × channel × category | map, category mix |
| `RFM` | `customer_rfm.csv` **related to** `customers.csv` on `customer_id` | customer | Use a *relationship* (noodle), not a join |
| `Products` | `products.csv` | product | optional top-products table |

After connecting:

* Set every `*_month`, `month`, `*_date` field to **Date** type.
* `Sales Geo[County Name]` → Geographic role **State/Province**; set **Map → Edit Locations → Country = Kenya**.
  Tableau recognises Kenya's 47 counties; fix any unmatched names in *Edit Locations*. `Unknown` can be excluded.
* Rename fields to Title Case (Tableau does this automatically for `snake_case`).
* Default number formats: currency fields → `KES #,##0` (custom: `"KES "#,##0`), rates → `Percentage, 1 dp`.

## 2. Parameters

| Name | Type | Values | Default |
|---|---|---|---|
| `p_Metric` | String, list | `Net Revenue`, `Orders`, `AOV`, `Gross Margin %` | `Net Revenue` |
| `p_Max Months` | Integer, range 0–23, step 1 | months since first order shown in the heatmap | `12` |

## 3. Calculated fields (Tableau syntax)

Create each in the data source named in brackets.

```tableau
// [Monthly Revenue] AOV
SUM([Net Revenue]) / SUM([Orders])

// [Monthly Revenue] Gross Margin %
SUM([Gross Profit]) / SUM([Net Revenue])

// [Monthly Revenue] Returning Revenue Share
SUM([Returning Customer Revenue]) / SUM([Net Revenue])

// [Monthly Revenue] Selected Metric
CASE [p_Metric]
    WHEN "Net Revenue"    THEN SUM([Net Revenue])
    WHEN "Orders"         THEN SUM([Orders])
    WHEN "AOV"            THEN SUM([Net Revenue]) / SUM([Orders])
    WHEN "Gross Margin %" THEN SUM([Gross Profit]) / SUM([Net Revenue])
END

// [Monthly Revenue] Revenue YoY %   (table calculation, compute using Order Month)
(ZN(SUM([Net Revenue])) - LOOKUP(ZN(SUM([Net Revenue])), -12))
    / ABS(LOOKUP(ZN(SUM([Net Revenue])), -12))

// [Monthly Revenue] Latest Month Flag  (used to drive KPI "vs last year" tiles)
[Order Month] = {FIXED : MAX([Order Month])}

// [Cohorts] Retention %   (weighted, so it is correct when cohorts are aggregated)
SUM([Active Customers]) / SUM([Cohort Size])

// [Cohorts] Cohort Label
STR(YEAR([Cohort Month])) + "-" + RIGHT("0" + STR(MONTH([Cohort Month])), 2)

// [Cohorts] In Month Window   (filter = True)
[Months Since First Order] <= [p_Max Months]

// [Cohorts] Cumulative Revenue per Customer   (table calc, compute along Months Since First Order)
RUNNING_SUM(SUM([Net Revenue])) / SUM([Cohort Size])

// [Channels] CAC
SUM([Marketing Spend]) / SUM([New Customers])

// [Channels] ROAS
SUM([Net Revenue]) / SUM([Marketing Spend])

// [Channels] First-Order ROAS
SUM([First Order Revenue]) / SUM([Marketing Spend])

// [Channels] Channel Label
UPPER(LEFT([Channel], 1)) + MID([Channel], 2)

// [Sales Geo] Revenue Share
SUM([Net Revenue]) / TOTAL(SUM([Net Revenue]))

// [Sales Geo] Gross Margin %
SUM([Gross Profit]) / SUM([Net Revenue])

// [RFM] Revenue Share
SUM([Monetary]) / TOTAL(SUM([Monetary]))

// [RFM] Customer Share
COUNTD([Customer Id]) / TOTAL(COUNTD([Customer Id]))

// [RFM] Segment Group   (for colour)
CASE [Rfm Segment]
    WHEN "Champions"        THEN "Grow"
    WHEN "Loyal Customers"  THEN "Grow"
    WHEN "Potential Loyalists" THEN "Nurture"
    WHEN "New Customers"    THEN "Nurture"
    WHEN "Needs Attention"  THEN "Nurture"
    WHEN "Cannot Lose Them" THEN "Win back"
    WHEN "At Risk"          THEN "Win back"
    ELSE "Low priority"
END
```

## 4. Colours (fixed, apply in every sheet)

| Channel | Hex |
|---|---|
| Web | `#2a78d6` |
| App | `#eb6834` |
| Store | `#1baf7a` |

New vs returning: New `#eb6834`, Returning `#2a78d6`. Heatmap and map: sequential **Blue** palette,
light → dark, range fixed 0–60 % for retention. Segment Group: Grow `#2a78d6`, Nurture `#1baf7a`,
Win back `#eb6834`, Low priority `#b4b2a9`. No dual axes anywhere.

## 5. Sheets

| # | Sheet | Source | Build |
|---|---|---|---|
| 1 | **KPI – Net Revenue** | Monthly Revenue | Text mark: `SUM([Net Revenue])` big, sub-line `Revenue YoY %` for the latest month. Repeat as sheets 1b–1e for **Orders**, **AOV**, **Gross Margin %**, **New Customers** (`SUM([New Customers])`). |
| 2 | **Revenue Trend** | Monthly Revenue | Columns `MONTH(Order Month)` (continuous). Rows: Measure Values = `New Customer Revenue`, `Returning Customer Revenue`. Mark: Bar, stacked; Colour: Measure Names. Tooltip adds AOV, Orders, Revenue YoY %. |
| 3 | **Metric Trend** | Monthly Revenue | Line of `Selected Metric` by `MONTH(Order Month)`; show `p_Metric` parameter control. |
| 4 | **Cohort Heatmap** | Cohorts | Columns `Months Since First Order` (discrete), Rows `Cohort Label`. Mark: Square; Colour `Retention %`; Label `Retention %`. Filter `In Month Window = True`. |
| 5 | **Retention Curve** | Cohorts | Columns `Months Since First Order` (continuous), Rows `Retention %` (weighted). Line. Optional colour by `YEAR(Cohort Month)` (2 lines). |
| 6 | **CAC by Channel** | Channels | Columns `Channel Label`, Rows `CAC`. Bar, colour by channel, label `KES #,##0`. |
| 7 | **ROAS by Channel** | Channels | Columns `Channel Label`, Rows `ROAS`. Bar, colour by channel, label `0.0"x"`. Tooltip: First-Order ROAS, Marketing Spend. |
| 8 | **CAC Trend** | Channels | Columns `QUARTER(Month)`, Rows `CAC`, colour Channel Label. Line. |
| 9 | **County Map** | Sales Geo | Filled map, Detail `County Name`, Colour `SUM([Net Revenue])` (Blue). Tooltip: Region, Revenue Share, Gross Margin %. Exclude `Unknown`. |
| 10 | **Region Bar** | Sales Geo | Rows `Region` sorted by revenue desc, Columns `SUM([Net Revenue])`. Bar. (Fallback if the map cannot geocode.) |
| 11 | **Category Mix** | Sales Geo | Scatter: Columns `Revenue Share`, Rows `Gross Margin %`, Detail `Category`, Label `Category`. Shows Electronics = high revenue / low margin. |
| 12 | **RFM Segments** | RFM | Rows `Rfm Segment` sorted by Revenue Share desc; Columns Measure Values `Customer Share`, `Revenue Share` (side-by-side bars). Colour Measure Names. |

## 6. Filters (global — "Apply to worksheets → All using related data sources")

* **Order Month / Month / Cohort Month** – range of dates, shown as a slider at the top of each dashboard.
  Create on `Monthly Revenue[Order Month]`, then on each other source use *Data → Edit Blend Relationships*
  or separate date filters bound to the same range.
* **Channel** – multi-select dropdown (Sales Geo + Channels).
* **Region** – multi-select dropdown (Sales Geo and RFM both carry `Region`).
* **Category** – multi-select dropdown (Sales Geo).
* Dashboard actions: clicking a **Region** bar or county on the map filters Category Mix;
  clicking a channel bar in sheet 6/7 highlights the same channel in sheet 8.

## 7. Dashboards & layout (fixed size 1200 × 900, Tableau Public default fonts)

**Dashboard 1 – Executive Overview**

```
+--------------------------------------------------------------------------+
| Title: Kenya Retail Sales Analytics (synthetic)       [Date slider]      |
+-----------+-----------+-----------+-----------+--------------------------+
| KPI Rev   | KPI Orders| KPI AOV   | KPI GM %  | KPI New Customers        |  h=110
+-----------+-----------+-----------+-----------+--------------------------+
| Revenue Trend (sheet 2)                              | Region Bar (10)   |  h=380
+------------------------------------------------------+-------------------+
| County Map (9)                     | Category Mix (11)                    |  h=330
+------------------------------------+--------------------------------------+
| Footnote: "Synthetic data generated for a portfolio project. Source: dbt marts." |
```

**Dashboard 2 – Customers & Retention**: Cohort Heatmap (4) left 60 % width full height;
right column Retention Curve (5) on top, RFM Segments (12) below; `p_Max Months` control top-right.

**Dashboard 3 – Channel Economics**: CAC by Channel (6) and ROAS by Channel (7) side-by-side on top,
CAC Trend (8) full width below, Channel filter top-right. Caption: *"CAC = paid media spend ÷ new customers
acquired in the channel; ROAS = channel net revenue ÷ spend."*

Use a **Story** or navigation buttons to move between the three dashboards.

## 8. Publish checklist

1. Values on Dashboard 1 should match the README (e.g. total net revenue **KES 600.1M**, AOV **KES 4,410**).
2. Add "Synthetic data" in the title and footer.
3. Publish to Tableau Public profile; set the thumbnail to Dashboard 1.
4. Paste the URL into the README placeholder and save a screenshot as `docs/images/tableau_dashboard.png`.
