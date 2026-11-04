#!/usr/bin/env python3
"""
Generate SYNTHETIC raw data for a fictional Kenyan multi-channel retailer.

Everything produced here is fake: names, phone numbers, emails and sales figures are
randomly generated (seeded, so runs are reproducible). The data is deliberately "dirty"
in the ways real source systems are, so that the dbt staging layer has real work to do:

  * duplicate rows (customer re-syncs, M-Pesa callback replays, double-loaded spend)
  * NULLs (missing county, email, product cost, delivery county)
  * inconsistent casing / whitespace ("Web", " APP", "M-Pesa", "MPESA", "nairobi ")
  * amounts stored as text ("KES 1,250.00", "1,234,567")
  * mixed phone formats (07..., 254..., +254 7.. ...)
  * zero-quantity order lines and an unknown promo code

Outputs (CSV):
  data/raw/{customers,products,orders,order_items,payments,marketing_spend}.csv
  data/sample/<same>.csv  -> small, referentially-consistent extract that IS committed
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")
DAYS = pd.date_range(START, END, freq="D")
N_DAYS = len(DAYS)
CHANNELS = np.array(["web", "app", "store"])

# --------------------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------------------
# 2019-census-ish populations (millions) x an e-commerce/urban factor -> customer weights
COUNTY_POP = {
    "Nairobi": 4.40, "Kiambu": 2.42, "Nakuru": 2.16, "Kakamega": 1.87, "Bungoma": 1.67,
    "Meru": 1.55, "Kilifi": 1.45, "Machakos": 1.42, "Kisii": 1.27, "Mombasa": 1.21,
    "Narok": 1.16, "Kisumu": 1.16, "Uasin Gishu": 1.16, "Kitui": 1.14, "Kajiado": 1.12,
    "Homa Bay": 1.13, "Migori": 1.12, "Mandera": 0.87, "Murang'a": 1.06, "Siaya": 0.99,
    "Makueni": 0.99, "Trans Nzoia": 0.99, "Kericho": 0.90, "Turkana": 0.93, "Bomet": 0.88,
    "Busia": 0.89, "Nandi": 0.89, "Kwale": 0.87, "Garissa": 0.84, "Wajir": 0.78,
    "Nyeri": 0.76, "Vihiga": 0.59, "Nyamira": 0.61, "Baringo": 0.67, "Embu": 0.61,
    "West Pokot": 0.62, "Kirinyaga": 0.61, "Nyandarua": 0.64, "Laikipia": 0.52,
    "Elgeyo Marakwet": 0.45, "Tharaka Nithi": 0.39, "Marsabit": 0.46, "Taita Taveta": 0.34,
    "Tana River": 0.32, "Samburu": 0.31, "Isiolo": 0.27, "Lamu": 0.14,
}
URBAN_BOOST = {"Nairobi": 3.0, "Mombasa": 2.0, "Kiambu": 1.8, "Kisumu": 1.7, "Nakuru": 1.6,
               "Uasin Gishu": 1.5, "Kajiado": 1.4, "Machakos": 1.3, "Nyeri": 1.2}

FIRST_NAMES = ["Wanjiru", "Achieng", "Kamau", "Otieno", "Mwangi", "Njeri", "Wambui", "Kiprono",
               "Chebet", "Akinyi", "Ochieng", "Muthoni", "Kariuki", "Wairimu", "Omondi", "Atieno",
               "Kibet", "Jepkosgei", "Mutua", "Mwende", "Nduta", "Brian", "Faith", "Kevin", "Mercy",
               "Dennis", "Esther", "Collins", "Grace", "Ian", "Joy", "Victor", "Sharon", "Ann",
               "John", "Mary", "Peter", "Lucy", "James", "Caroline", "Hassan", "Amina", "Fatuma",
               "Ali", "Halima", "Wekesa", "Nafula", "Wafula", "Moraa", "Kerubo", "Nyambura", "Zawadi"]
LAST_NAMES = ["Kamau", "Otieno", "Mwangi", "Odhiambo", "Kipchoge", "Wanjiku", "Njoroge", "Ochieng",
              "Mutua", "Kiprotich", "Wekesa", "Barasa", "Omondi", "Koech", "Cheruiyot", "Muriuki",
              "Nyaga", "Gitau", "Onyango", "Owino", "Mohamed", "Hassan", "Abdi", "Kariuki", "Waweru",
              "Ndungu", "Korir", "Rotich", "Langat", "Juma", "Nyamweya", "Makori", "Simiyu", "Mbugua"]

# category -> (n_products, cost_ratio, [(item, typical KES shelf price), ...])
CATEGORIES = {
    "Groceries": (90, 0.82, [("Maize Flour 2kg", 190), ("Wheat Flour 2kg", 210), ("Pishori Rice 1kg", 260),
                  ("Sugar 1kg", 170), ("Cooking Oil 1L", 330), ("Cooking Oil 3L", 950), ("Tea Leaves 250g", 160),
                  ("Fresh Milk 500ml", 65), ("Long-life Milk 1L", 140), ("Eggs Tray 30", 480), ("Bread 400g", 65),
                  ("Green Grams 1kg", 220), ("Beans 1kg", 200), ("Spaghetti 500g", 130), ("Tomato Paste 400g", 180),
                  ("Salt 1kg", 50), ("Margarine 500g", 260), ("Peanut Butter 400g", 380)]),
    "Beverages": (40, 0.78, [("Soda 500ml", 70), ("Soda 2L", 210), ("Juice 1L", 230), ("Mineral Water 1.5L", 90),
                  ("Instant Coffee 100g", 650), ("Drinking Chocolate 400g", 520), ("Energy Drink 500ml", 120),
                  ("Ground Coffee 250g", 600)]),
    "Household": (35, 0.72, [("Laundry Bar 800g", 170), ("Washing Powder 1kg", 320), ("Dish Liquid 750ml", 230),
                  ("Toilet Paper 10pk", 420), ("Bleach 1L", 190), ("Insecticide 300ml", 450), ("Floor Cleaner 1L", 280)]),
    "Personal Care": (40, 0.65, [("Bathing Soap 3pk", 250), ("Toothpaste 140g", 190), ("Body Lotion 400ml", 480),
                      ("Shampoo 400ml", 550), ("Petroleum Jelly 250ml", 220), ("Deodorant 150ml", 420),
                      ("Sanitary Pads 8pk", 130)]),
    "Baby & Kids": (25, 0.70, [("Diapers 40pk", 1450), ("Baby Wipes 80pk", 380), ("Baby Formula 400g", 1650),
                    ("Baby Lotion 200ml", 420), ("School Bag", 1800), ("Exercise Books 10pk", 450)]),
    "Home & Kitchen": (30, 0.62, [("Sufuria Set", 3200), ("Thermos Flask 1.8L", 1500), ("Electric Kettle", 2400),
                       ("Non-stick Pan", 1900), ("Blender", 5500), ("Gas Refill 6kg", 1350), ("Plastic Basin", 350),
                       ("Duvet Double", 4200)]),
    "Fashion": (20, 0.50, [("Kitenge Dress", 2500), ("Men's Shirt", 1600), ("Jeans", 2200), ("Sneakers", 3500),
                ("Leso Pair", 700), ("School Uniform Set", 2800), ("Rubber Sandals", 450)]),
    "Electronics": (20, 0.86, [("Smartphone 64GB", 14500), ("Feature Phone", 2200), ("Solar Lamp Kit", 3800),
                    ("Bluetooth Speaker", 3500), ('32" LED TV', 18500), ("Power Bank 20000mAh", 2600),
                    ("Earphones", 900), ('Smart TV 43"', 38000)]),
}
BRANDS = ["Savanna", "Tausi", "Jua", "Baraka", "Neema", "Simba", "Kifaru", "Mvua", "Pwani", "Nyota"]

PROMOS = [  # code, discount, start, end (inclusive) -- mirrors seeds/promo_codes.csv
    ("BACK2SCHOOL24", 0.10, "2024-01-02", "2024-01-21"), ("EASTER24", 0.15, "2024-03-25", "2024-04-01"),
    ("MADARAKA24", 0.10, "2024-05-30", "2024-06-02"), ("BLACKFRIDAY24", 0.25, "2024-11-29", "2024-12-02"),
    ("JAMHURI24", 0.20, "2024-12-10", "2024-12-14"), ("BACK2SCHOOL25", 0.10, "2025-01-02", "2025-01-20"),
    ("EASTER25", 0.15, "2025-04-14", "2025-04-21"), ("MADARAKA25", 0.10, "2025-05-30", "2025-06-02"),
    ("BLACKFRIDAY25", 0.25, "2025-11-28", "2025-12-01"), ("JAMHURI25", 0.20, "2025-12-10", "2025-12-14"),
]
WELCOME_CODE, WELCOME_PCT = "KARIBU10", 0.10

# Channel behaviour
P_ONE_TIME = {"web": 0.36, "app": 0.27, "store": 0.40}
REPEAT_RATE_30D = {"web": 1.50, "app": 2.20, "store": 1.40}
BASKET_LAMBDA = {"web": 1.6, "app": 1.2, "store": 2.6}
CAT_MIX = {  # category probabilities by channel (same order as CATEGORIES)
    "store": [0.40, 0.15, 0.13, 0.12, 0.06, 0.06, 0.04, 0.04],
    "web":   [0.22, 0.08, 0.10, 0.12, 0.08, 0.12, 0.14, 0.14],
    "app":   [0.32, 0.12, 0.12, 0.14, 0.08, 0.08, 0.08, 0.06],
}
TARGET_CAC = {"web": 1900.0, "app": 1250.0, "store": 2700.0}  # KES, used to back out spend


def dirty_case(rng: np.random.Generator, values: np.ndarray, p: float = 0.15) -> np.ndarray:
    """Randomly upper/title-case and pad a fraction of string values."""
    out = values.astype(object).copy()
    idx = np.where(rng.random(len(out)) < p)[0]
    kinds = rng.integers(0, 4, len(idx))
    for i, k in zip(idx, kinds):
        v = out[i]
        if v is None or (isinstance(v, float) and np.isnan(v)):
            continue
        out[i] = [str(v).upper(), str(v).title(), f" {v}", f"{v} "][k]
    return out


def day_weights() -> np.ndarray:
    season = np.array([0.85, 0.85, 0.95, 1.0, 0.95, 0.95, 0.95, 1.0, 0.95, 1.0, 1.15, 1.35])[DAYS.month - 1]
    dom = DAYS.day.values
    payday = np.where((dom >= 25) | (dom <= 3), 1.2, 1.0)  # salary-week effect
    weekend = np.where(DAYS.dayofweek.values >= 5, 1.1, 1.0)
    bf = np.ones(N_DAYS)
    for d in ["2024-11-29", "2025-11-28"]:
        bf[(DAYS >= pd.Timestamp(d)) & (DAYS <= pd.Timestamp(d) + pd.Timedelta(days=3))] = 1.8
    return season * payday * weekend * bf


def sample_days_in_window(rng, cum0: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Sample one day index in [a, b] per row, proportional to daily weights (inverse CDF)."""
    u = rng.uniform(cum0[a], cum0[b + 1])
    return np.clip(np.searchsorted(cum0, u, side="right") - 1, a, b)


def fmt_phone(rng, n):
    nine = np.char.add(rng.choice(["7", "1"], n, p=[0.85, 0.15]), rng.integers(10_000_000, 99_999_999, n).astype(str))
    fmt = rng.integers(0, 4, n)
    out = np.empty(n, dtype=object)
    for i, (s, f) in enumerate(zip(nine, fmt)):
        out[i] = [f"0{s}", f"254{s}", f"+254 {s[:3]} {s[3:6]} {s[6:]}", f"+254-{s}"][f]
    return out


# --------------------------------------------------------------------------------------
def build(n_customers: int, seed: int):
    rng = np.random.default_rng(seed)
    w = day_weights()
    cum0 = np.concatenate([[0.0], np.cumsum(w)])

    # ---------------- products ----------------
    prows, cat_product_idx = [], {}
    pid = 0
    for cat, (n, cost_ratio, items) in CATEGORIES.items():
        idxs = []
        for j in range(n):
            pid += 1
            item, base = items[j % len(items)]
            brand = BRANDS[(j // len(items) + j) % len(BRANDS)]
            price = base * rng.uniform(0.85, 1.20)
            price = float(round(price, -1) - 1 if price > 100 else round(price))
            cost = round(price * cost_ratio * rng.uniform(0.92, 1.08), 2)
            prows.append(dict(product_id=f"P{pid:04d}", product_name=f"{brand} {item}", category=cat,
                              list_price=price, unit_cost=cost,
                              is_active=bool(rng.random() > 0.04), created_at="2023-12-01"))
            idxs.append(pid - 1)
        cat_product_idx[cat] = np.array(idxs)
    products = pd.DataFrame(prows)

    # ---------------- customers ----------------
    trend = np.linspace(1.0, 1.9, N_DAYS)  # business growing ~90% over two years
    p_signup = (trend * np.sqrt(w)) / (trend * np.sqrt(w)).sum()
    signup_day = np.sort(rng.choice(N_DAYS, n_customers, p=p_signup))
    t = signup_day / (N_DAYS - 1)
    p_app = 0.24 + 0.22 * t
    p_store = 0.36 - 0.14 * t
    u = rng.random(n_customers)
    signup_channel = np.where(u < p_app, "app", np.where(u < p_app + p_store, "store", "web"))

    counties = np.array(list(COUNTY_POP))
    cw = np.array([COUNTY_POP[c] * URBAN_BOOST.get(c, 1.0) for c in counties])
    county = rng.choice(counties, n_customers, p=cw / cw.sum())
    fn = rng.choice(FIRST_NAMES, n_customers)
    ln = rng.choice(LAST_NAMES, n_customers)
    cust_ids = np.array([f"C{i:06d}" for i in range(1, n_customers + 1)])
    customers = pd.DataFrame(dict(
        customer_id=cust_ids, first_name=fn, last_name=ln,
        email=[f"{a.lower()}.{b.lower()}{i}@example.co.ke" for i, (a, b) in enumerate(zip(fn, ln))],
        phone=fmt_phone(rng, n_customers), county=county,
        signup_date=DAYS[signup_day].strftime("%Y-%m-%d"), signup_channel=signup_channel,
        marketing_opt_in=rng.random(n_customers) < 0.62,
        updated_at=(DAYS[signup_day] + pd.to_timedelta(rng.integers(0, 86400, n_customers), unit="s")).strftime("%Y-%m-%d %H:%M:%S"),
    ))

    # ---------------- orders (customer lifecycles) ----------------
    lag = rng.geometric(0.35, n_customers) - 1
    first_day = signup_day + lag
    has_order = first_day <= N_DAYS - 1
    one_time = rng.random(n_customers) < np.vectorize(P_ONE_TIME.get)(signup_channel)
    life = rng.exponential(300, n_customers)
    end_day = np.minimum(first_day + life, N_DAYS - 1).astype(int)
    rate = np.vectorize(REPEAT_RATE_30D.get)(signup_channel) * rng.gamma(2.0, 0.5, n_customers)
    span = np.clip(end_day - first_day, 0, None)
    n_rep = np.where(one_time | ~has_order | (span < 1), 0, rng.poisson(rate * span / 30))

    c_first = np.where(has_order)[0]
    rep_cust = np.repeat(np.arange(n_customers), n_rep)
    rep_day = sample_days_in_window(rng, cum0, first_day[rep_cust] + 1, end_day[rep_cust])
    o_cust = np.concatenate([c_first, rep_cust])
    o_day = np.concatenate([first_day[c_first], rep_day])
    o_is_first = np.concatenate([np.ones(len(c_first), bool), np.zeros(len(rep_cust), bool)])
    n_orders = len(o_cust)

    pref = signup_channel[o_cust]
    other = rng.choice(CHANNELS, n_orders, p=[0.35, 0.40, 0.25])
    o_channel = np.where(o_is_first | (rng.random(n_orders) < 0.75), pref, other)

    hour = np.where(o_channel == "store", rng.integers(8, 21, n_orders),
                    np.clip(rng.normal(19, 3.5, n_orders).round(), 0, 23)).astype(int)
    ts = DAYS[o_day] + pd.to_timedelta(hour, unit="h") + pd.to_timedelta(rng.integers(0, 3600, n_orders), unit="s")

    o_county = county[o_cust].astype(object)
    moved = rng.random(n_orders) < 0.05
    o_county[moved] = rng.choice(counties, moved.sum(), p=cw / cw.sum())

    # status
    p_cancel = np.select([o_channel == "store"], [0.01], 0.045)
    p_return = np.select([o_channel == "store", o_channel == "web"], [0.015, 0.05], 0.04)
    r = rng.random(n_orders)
    status = np.where(r < p_cancel, "cancelled", np.where(r < p_cancel + p_return, "returned", "completed"))

    # payment method
    r = rng.random(n_orders)
    pay = np.where(o_channel == "store",
                   np.where(r < 0.55, "mpesa", np.where(r < 0.75, "card", "cash")),
                   np.where(r < 0.72, "mpesa", np.where(r < 0.97, "card", "cash")))

    # promos
    promo = np.full(n_orders, None, dtype=object)
    promo_pct = np.zeros(n_orders)
    welcome = o_is_first & (o_channel != "store") & (rng.random(n_orders) < 0.35)
    promo[welcome], promo_pct[welcome] = WELCOME_CODE, WELCOME_PCT
    for code, pct, s, e in PROMOS:
        in_win = (ts >= pd.Timestamp(s)) & (ts < pd.Timestamp(e) + pd.Timedelta(days=1))
        take = in_win & (promo == None) & (rng.random(n_orders) < 0.35)  # noqa: E711
        promo[take], promo_pct[take] = code, pct
    junk = (promo == None) & (rng.random(n_orders) < 0.002)  # noqa: E711  unknown code typed at checkout
    promo[junk] = "FREESHIP"

    orders = pd.DataFrame(dict(_cust=o_cust, ts=ts, channel=o_channel, county=o_county, status=status,
                               pay=pay, promo=promo, promo_pct=promo_pct, day=o_day))
    orders = orders.sort_values("ts", kind="stable").reset_index(drop=True)
    orders["order_id"] = [f"ORD{i:07d}" for i in range(1, len(orders) + 1)]

    # ---------------- order items ----------------
    lam = orders["channel"].map(BASKET_LAMBDA).to_numpy()
    k = 1 + rng.poisson(lam)
    it_order = np.repeat(np.arange(len(orders)), k)
    it_channel = orders["channel"].to_numpy()[it_order]
    cats = np.array(list(CATEGORIES))
    it_cat = np.empty(len(it_order), dtype=object)
    for ch in CHANNELS:
        m = it_channel == ch
        it_cat[m] = rng.choice(cats, m.sum(), p=CAT_MIX[ch])
    it_prod = np.empty(len(it_order), dtype=int)
    for cat in cats:
        m = it_cat == cat
        pool = cat_product_idx[cat]
        zw = 1 / np.arange(1, len(pool) + 1) ** 0.9
        it_prod[m] = rng.choice(pool, m.sum(), p=zw / zw.sum())
    bulk = np.isin(it_cat, ["Groceries", "Beverages", "Household"])
    qty = np.where(bulk, 1 + rng.poisson(1.2, len(it_order)),
                   np.where(it_cat == "Personal Care", 1 + rng.poisson(0.5, len(it_order)),
                            1 + rng.poisson(0.08, len(it_order))))
    unit_price = products["list_price"].to_numpy()[it_prod].astype(float)
    gross = unit_price * qty
    disc = np.round(gross * orders["promo_pct"].to_numpy()[it_order], 2)
    items = pd.DataFrame(dict(order_item_id=[f"OI{i:08d}" for i in range(1, len(it_order) + 1)],
                              order_id=orders["order_id"].to_numpy()[it_order],
                              product_id=products["product_id"].to_numpy()[it_prod],
                              quantity=qty, unit_price=unit_price, discount_amount=disc))
    order_net = pd.Series(gross - disc).groupby(it_order).sum().round(2).to_numpy()

    # ---------------- payments ----------------
    prow = []
    pid = 0
    o_ts = orders["ts"].to_numpy()
    rr = rng.random((len(orders), 3))
    for i, (st, pm) in enumerate(zip(orders["status"].to_numpy(), orders["pay"].to_numpy())):
        base = pd.Timestamp(o_ts[i])
        amt = order_net[i]
        if st == "cancelled":
            if rr[i, 0] < 0.6:
                pid += 1
                prow.append((pid, i, pm, amt, "failed", base + pd.Timedelta(minutes=2)))
            continue
        if pm == "mpesa" and rr[i, 1] < 0.07:  # STK push timed out, customer retried
            pid += 1
            prow.append((pid, i, pm, amt, "failed", base + pd.Timedelta(minutes=1)))
        pid += 1
        prow.append((pid, i, pm, amt, "success", base + pd.Timedelta(minutes=3)))
        if st == "returned":
            pid += 1
            prow.append((pid, i, pm, amt, "refunded", base + pd.Timedelta(days=int(3 + rr[i, 2] * 11))))
    pay_df = pd.DataFrame(prow, columns=["pid", "oi", "method", "amount", "status", "ts"])
    payments = pd.DataFrame(dict(
        payment_id=[f"PAY{p:08d}" for p in pay_df["pid"]],
        order_id=orders["order_id"].to_numpy()[pay_df["oi"]],
        payment_method=pay_df["method"], amount_kes=pay_df["amount"], payment_status=pay_df["status"],
        paid_at=pd.to_datetime(pay_df["ts"]).dt.strftime("%Y-%m-%d %H:%M:%S")))

    # ---------------- marketing spend (backed out of realised acquisitions) ----------------
    first_ch = orders.loc[~orders.duplicated("_cust"), ["ts", "channel"]]
    acq = first_ch.groupby([first_ch["ts"].dt.to_period("M"), "channel"]).size()
    mrows = []
    months = pd.period_range("2024-01", "2025-12", freq="M")
    campaigns = {"web": [("search", 0.55), ("social", 0.45)], "app": [("app_install", 0.65), ("social", 0.35)],
                 "store": [("radio", 0.45), ("outdoor", 0.30), ("in_store_promo", 0.25)]}
    for mi, mth in enumerate(months):
        for ch in CHANNELS:
            n_new = acq.get((mth, ch), 0)
            drift = {"app": 1.0 - 0.25 * mi / 23, "web": 1.0 + 0.10 * mi / 23, "store": 1.0}[ch]
            total = n_new * TARGET_CAC[ch] * drift * rng.uniform(0.85, 1.15)
            for camp, share in campaigns[ch]:
                mrows.append(dict(month=str(mth), channel=ch, campaign_type=camp,
                                  spend_kes=round(total * share * rng.uniform(0.9, 1.1), 0)))
    spend = pd.DataFrame(mrows)

    # ---------------- raw-format output + deliberate dirt ----------------
    orders_raw = pd.DataFrame(dict(
        order_id=orders["order_id"], customer_id=cust_ids[orders["_cust"].to_numpy()],
        order_ts=orders["ts"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        channel=dirty_case(rng, orders["channel"].to_numpy(), 0.12),
        delivery_county=dirty_case(rng, orders["county"].to_numpy(), 0.10),
        payment_method=orders["pay"].to_numpy(), promo_code=orders["promo"].to_numpy(),
        order_status=dirty_case(rng, orders["status"].to_numpy(), 0.08)))
    pm_variants = {"mpesa": ["M-Pesa", "MPESA", "mpesa", "Mpesa", "M-PESA"],
                   "card": ["card", "Card", "VISA", "Mastercard"], "cash": ["cash", "Cash", "CASH"]}
    for col_df in (orders_raw, payments):
        col = "payment_method"
        col_df[col] = [pm_variants[v][rng.integers(len(pm_variants[v]))] for v in col_df[col]]
    m = rng.random(len(orders_raw)) < 0.01
    orders_raw.loc[m, "delivery_county"] = None
    pm = orders_raw["promo_code"].notna() & (rng.random(len(orders_raw)) < 0.08)
    orders_raw.loc[pm, "promo_code"] = orders_raw.loc[pm, "promo_code"].str.lower().map(lambda s: f" {s} ")
    orders_raw["_loaded_at"] = orders_raw["order_ts"]
    dup = orders_raw.sample(frac=0.005, random_state=seed).assign(_loaded_at="2026-01-01 02:00:00")
    orders_raw = pd.concat([orders_raw, dup]).sort_values("order_id", kind="stable")

    customers["county"] = dirty_case(rng, customers["county"].to_numpy(), 0.15)
    customers.loc[rng.random(len(customers)) < 0.02, "county"] = None
    customers.loc[rng.random(len(customers)) < 0.03, "email"] = None
    em = customers["email"].notna() & (rng.random(len(customers)) < 0.05)
    customers.loc[em, "email"] = customers.loc[em, "email"].str.upper()
    customers["signup_channel"] = dirty_case(rng, customers["signup_channel"].to_numpy(), 0.10)
    cdup = customers.sample(frac=0.015, random_state=seed).copy()
    cdup["updated_at"] = "2026-01-05 08:00:00"  # later CRM re-sync: latest version must win
    customers = pd.concat([customers, cdup]).sort_values("customer_id", kind="stable")

    products["category"] = dirty_case(rng, products["category"].to_numpy(), 0.12)
    products.loc[rng.random(len(products)) < 0.05, "unit_cost"] = None
    txt = rng.random(len(products)) < 0.10
    products["list_price"] = products["list_price"].astype(object)
    products.loc[txt, "list_price"] = products.loc[txt, "list_price"].map(lambda v: f"KES {v:,.2f}")

    zero = rng.random(len(items)) < 0.003
    items.loc[zero, "quantity"] = 0
    items = pd.concat([items, items.sample(frac=0.002, random_state=seed)]).sort_values("order_item_id", kind="stable")

    payments = pd.concat([payments, payments.sample(frac=0.003, random_state=seed)])  # M-Pesa callback replays
    payments = payments.sort_values("payment_id", kind="stable")

    spend["channel"] = dirty_case(rng, spend["channel"].to_numpy(), 0.2)
    big = spend["spend_kes"] > 100_000
    spend["spend_kes"] = spend["spend_kes"].astype(object)
    spend.loc[big, "spend_kes"] = spend.loc[big, "spend_kes"].map(lambda v: f"{v:,.0f}")
    spend = pd.concat([spend, spend.sample(n=3, random_state=seed)])  # double-loaded rows

    return dict(customers=customers, products=products, orders=orders_raw, order_items=items,
                payments=payments, marketing_spend=spend)


def write_sample(tables: dict, out: Path, n: int = 200, seed: int = 42):
    """Referentially-consistent ~n-row extract for the repo (raw files are gitignored)."""
    out.mkdir(parents=True, exist_ok=True)
    o = tables["orders"].drop_duplicates("order_id").sample(n=n, random_state=seed)
    ids = set(o["order_id"])
    c = tables["customers"][tables["customers"]["customer_id"].isin(o["customer_id"])]
    oi = tables["order_items"][tables["order_items"]["order_id"].isin(ids)].head(n)
    p = tables["products"][tables["products"]["product_id"].isin(oi["product_id"])]
    pay = tables["payments"][tables["payments"]["order_id"].isin(ids)].head(n)
    sample = dict(customers=c.head(n), products=p.head(n), orders=o.sort_values("order_id"),
                  order_items=oi, payments=pay, marketing_spend=tables["marketing_spend"].head(n))
    for name, df in sample.items():
        df.to_csv(out / f"{name}.csv", index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--customers", type=int, default=20_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "raw")
    ap.add_argument("--no-sample", action="store_true", help="skip writing data/sample/")
    args = ap.parse_args()

    tables = build(args.customers, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(args.out / f"{name}.csv", index=False)
        print(f"  {name:<16} {len(df):>9,} rows -> {args.out / (name + '.csv')}")
    if not args.no_sample:
        write_sample(tables, ROOT / "data" / "sample", seed=args.seed)
        print(f"  sample extract     -> {ROOT / 'data' / 'sample'}")


if __name__ == "__main__":
    main()
