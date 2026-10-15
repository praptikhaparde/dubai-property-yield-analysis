import os, sqlite3
import pandas as pd

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/")
conn = sqlite3.connect(base + "data/clean/dubai_property.db")
s = pd.read_sql("""SELECT area_id, area_name_en, price_per_sqft, area_sqft, instance_date FROM sales
                   WHERE property_sub_type_en='Flat' AND reg_type_en='Existing Properties'""",
                conn, parse_dates=["instance_date"])
r = pd.read_sql("""SELECT area_id, rent_per_sqft, contract_start_date FROM rent
                   WHERE ejari_property_type_en='Flat' AND contract_reg_type_en='New'""",
                conn, parse_dates=["contract_start_date"])
conn.close()

s["yr"] = s["instance_date"].dt.year
r["yr"] = r["contract_start_date"].dt.year
s["price_aed"] = s["price_per_sqft"] * s["area_sqft"]
names = s.groupby("area_id")["area_name_en"].agg(lambda x: x.mode().iloc[0])

sp = s.groupby(["area_id", "yr"]).agg(deals=("price_per_sqft", "size"),
        price=("price_per_sqft", "median"), median_price_aed=("price_aed", "median")).reset_index()
rp = r.groupby(["area_id", "yr"]).agg(rents=("rent_per_sqft", "size"),
        rent=("rent_per_sqft", "median")).reset_index()
d = sp.merge(rp, on=["area_id", "yr"])
d = d[(d["deals"] >= 30) & (d["rents"] >= 30)]
d["yield_pct"] = 100 * d["rent"] / d["price"]

a = d[d["yr"] == 2023].set_index("area_id")
b = d[d["yr"] == 2025].set_index("area_id")
t = b[["deals", "rents", "price", "rent", "yield_pct", "median_price_aed"]].join(
    a[["price", "deals"]].rename(columns={"price": "price_2023", "deals": "deals_2023"}), how="inner")
t = t[(t["deals"] >= 100) & (t["rents"] >= 100) & (t["deals_2023"] >= 100)].copy()
t["growth_pct"] = 100 * (t["price"] / t["price_2023"] - 1)
t["area"] = names

t["income_score"] = 100 * t["yield_pct"].rank(pct=True)
t["growth_score"] = 100 * t["growth_pct"].rank(pct=True)
t["balanced_score"] = 0.6 * t["income_score"] + 0.4 * t["growth_score"]
print("Areas eligible (100+ sales and rents in 2025, 100+ sales in 2023):", len(t))

def recommend(profile, budget=None, n=3):
    col = {"income": "income_score", "growth": "growth_score", "balanced": "balanced_score"}[profile]
    x = t if budget is None else t[t["median_price_aed"] <= budget]
    x = x.sort_values(col, ascending=False).head(n)
    label = {"income": "INCOME", "growth": "GROWTH (past growth, not a forecast)", "balanced": "BALANCED"}[profile]
    print(f"\n  {label} investor:")
    if len(x) == 0:
        print("    no eligible area in this budget")
    for _, row in x.iterrows():
        warn = "  [!] weak price growth" if row["growth_pct"] < 10 else ""
        print(f"    {row['area']}: {row['yield_pct']:.1f}% yield, prices {row['growth_pct']:+.0f}% since 2023, "
              f"typical flat ~AED {row['median_price_aed']/1e6:.2f}M "
              f"({int(row['deals'])} sales in 2025, {int(row['deals_2023'])} in 2023){warn}")

for budget in [None, 500_000, 800_000, 1_200_000]:
    print("\n==== BUDGET:", "any" if budget is None else f"typical flat up to AED {budget:,}", "====")
    for p in ["income", "growth", "balanced"]:
        recommend(p, budget)

cols = ["area", "deals", "deals_2023", "rents", "price", "rent", "yield_pct", "growth_pct",
        "median_price_aed", "income_score", "growth_score", "balanced_score"]
t[cols].round(1).sort_values("balanced_score", ascending=False).to_csv(
    base + "data/clean/area_scores.csv")
print("\nSaved data/clean/area_scores.csv (this will feed your dashboard)")
