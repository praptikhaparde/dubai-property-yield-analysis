import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/")
conn = sqlite3.connect(base + "data/clean/dubai_property.db")

s = pd.read_sql("""SELECT area_id, area_name_en, price_per_sqft, instance_date FROM sales
                   WHERE property_sub_type_en='Flat' AND reg_type_en='Existing Properties'""",
                conn, parse_dates=["instance_date"])
r = pd.read_sql("""SELECT area_id, rent_per_sqft, contract_start_date FROM rent
                   WHERE ejari_property_type_en='Flat' AND contract_reg_type_en='New'""",
                conn, parse_dates=["contract_start_date"])
conn.close()

s["yr"] = s["instance_date"].dt.year
r["yr"] = r["contract_start_date"].dt.year

sp = s.groupby(["area_id", "yr"]).agg(deals=("price_per_sqft", "size"),
                                       price=("price_per_sqft", "median")).reset_index()
rp = r.groupby(["area_id", "yr"]).agg(rents=("rent_per_sqft", "size"),
                                       rent=("rent_per_sqft", "median")).reset_index()
names = s.groupby("area_id")["area_name_en"].agg(lambda x: x.mode().iloc[0])

d = sp.merge(rp, on=["area_id", "yr"])
d = d[(d["deals"] >= 30) & (d["rents"] >= 30)]
d["yield_pct"] = 100 * d["rent"] / d["price"]

a = d[d["yr"] == 2023].set_index("area_id")
b = d[d["yr"] == 2025].set_index("area_id")
out = a[["price", "yield_pct"]].join(b[["deals", "rents", "price", "rent", "yield_pct"]],
                                     lsuffix="_2023", rsuffix="_2025", how="inner")
out["growth_pct"] = 100 * (out["price_2025"] / out["price_2023"] - 1)
out["area"] = names
out = out.reset_index().sort_values("deals", ascending=False)
out.round(1).to_csv(base + "data/clean/area_summary.csv", index=False)

print(len(out), "areas with enough data in both 2023 and 2025\n")
print(out[["area", "deals", "price_2025", "yield_pct_2025", "growth_pct"]]
      .round(1).head(20).to_string(index=False))

top = out.head(25)
plt.figure(figsize=(11, 7))
plt.scatter(top["yield_pct_2025"], top["growth_pct"], s=top["deals"] / 8, alpha=0.5)
for _, row in top.iterrows():
    plt.annotate(row["area"], (row["yield_pct_2025"], row["growth_pct"]), fontsize=8)
plt.xlabel("Gross rental yield 2025 (%)")
plt.ylabel("Price per sqft growth, 2023 to 2025 (%)")
plt.title("Dubai flats: yield vs price growth (25 busiest areas, median-based)")
plt.tight_layout()
plt.savefig(base + "charts/yield_vs_growth.png", dpi=150)
print("\nChart saved in charts/yield_vs_growth.png")
