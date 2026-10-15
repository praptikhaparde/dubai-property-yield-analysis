import os, sqlite3
import numpy as np
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
names = s.groupby("area_id")["area_name_en"].agg(lambda x: x.mode().iloc[0])

sp = s.groupby(["area_id", "yr"]).agg(deals=("price_per_sqft", "size"),
                                       price=("price_per_sqft", "median")).reset_index()
rp = r.groupby(["area_id", "yr"]).agg(rents=("rent_per_sqft", "size"),
                                       rent=("rent_per_sqft", "median")).reset_index()
d = sp.merge(rp, on=["area_id", "yr"])
d = d[(d["deals"] >= 30) & (d["rents"] >= 30)]
d["yield_pct"] = 100 * d["rent"] / d["price"]

price = d.pivot(index="area_id", columns="yr", values="price")
yld = d.pivot(index="area_id", columns="yr", values="yield_pct")
ok = price[[2023, 2024, 2025]].dropna().index
price, yld = price.loc[ok], yld.loc[ok]
print("Areas with enough data in 2023, 2024 and 2025:", len(ok))

# What we could see at the end of 2024
g_form = 100 * (price[2024] / price[2023] - 1)
y_form = yld[2024]
# What happened in 2025
g_out = 100 * (price[2025] / price[2024] - 1)
y_out = yld[2025]
total_out = g_out + y_out

scores = {
    "Income picks (top yield 2024)": y_form,
    "Growth picks (top growth 2023-24)": g_form,
    "Balanced picks (yield + growth)": y_form.rank(pct=True) + g_form.rank(pct=True),
}
k = max(5, len(ok) // 3)
rows = []
for label, sc in scores.items():
    picks = sc.sort_values(ascending=False).head(k).index
    rest = sc.index.difference(picks)
    rows.append({"strategy": label, "n_picks": k,
                 "picks_price_growth_2025": g_out[picks].mean(),
                 "picks_yield_2025": y_out[picks].mean(),
                 "picks_total_2025": total_out[picks].mean(),
                 "rest_total_2025": total_out[rest].mean(),
                 "all_areas_total_2025": total_out.mean()})
res = pd.DataFrame(rows).round(1)
print("\nBACKTEST: picks made with 2023-2024 data, judged on 2025")
print("(total = price growth % + gross yield %)\n")
print(res.to_string(index=False))

print("\nDoes last year predict next year? (rank correlation, -1 to +1)")
print("  Yield 2024 vs yield 2025:       ", round(y_form.rank().corr(y_out.rank()), 2))
print("  Growth 2023-24 vs growth 2025:  ", round(g_form.rank().corr(g_out.rank()), 2))

bal = scores["Balanced picks (yield + growth)"].sort_values(ascending=False).head(k).index
print("\nBalanced picks:")
print(pd.DataFrame({"area": names[bal], "yield_2024": y_form[bal].round(1),
      "growth_23_24": g_form[bal].round(1), "growth_2025": g_out[bal].round(1)}).to_string(index=False))

out = pd.DataFrame({"area": names[ok], "yield_2024": y_form, "growth_2023_24": g_form,
                    "yield_2025": y_out, "growth_2025": g_out, "total_2025": total_out}).round(1)
out.to_csv(base + "data/clean/backtest_areas.csv")
res.to_csv(base + "data/clean/backtest_summary.csv", index=False)

x = np.arange(len(res)); w = 0.27
plt.figure(figsize=(10, 6))
plt.bar(x - w, res["picks_total_2025"], w, label="Our picks")
plt.bar(x, res["rest_total_2025"], w, label="Other areas")
plt.bar(x + w, res["all_areas_total_2025"], w, label="All areas")
plt.xticks(x, [t.split(" (")[0] for t in res["strategy"]])
plt.ylabel("2025 total return (price growth + yield, %)")
plt.title("Backtest: did picks made in 2024 beat the market in 2025?")
plt.legend()
plt.tight_layout()
plt.savefig(base + "charts/backtest.png", dpi=150)
print("\nSaved: backtest_areas.csv, backtest_summary.csv, charts/backtest.png")
