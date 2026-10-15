import os, sqlite3
import pandas as pd

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/")
conn = sqlite3.connect(base + "data/clean/dubai_property.db")
s = pd.read_sql("""SELECT area_id, area_name_en, price_per_sqft, instance_date FROM sales
                   WHERE property_sub_type_en='Flat' AND reg_type_en='Existing Properties'""",
                conn, parse_dates=["instance_date"])
r = pd.read_sql("""SELECT area_id, rent_per_sqft, contract_start_date FROM rent
                   WHERE ejari_property_type_en='Flat' AND contract_reg_type_en='New'""",
                conn, parse_dates=["contract_start_date"])
conn.close()

raw = pd.read_csv(base + "data/raw/transactions_2026-10-07_17-55-58_0001.csv",
                  usecols=["area_id", "master_project_en"])
label = (raw.dropna(subset=["master_project_en"])
            .groupby("area_id")["master_project_en"].agg(lambda x: x.mode().iloc[0]))

s["year"] = s["instance_date"].dt.year
r["year"] = r["contract_start_date"].dt.year
names = s.groupby("area_id")["area_name_en"].agg(lambda x: x.mode().iloc[0])

sp = s.groupby(["area_id", "year"]).agg(sales=("price_per_sqft", "size"),
                                         price_per_sqft=("price_per_sqft", "median")).reset_index()
rp = r.groupby(["area_id", "year"]).agg(rent_contracts=("rent_per_sqft", "size"),
                                         rent_per_sqft=("rent_per_sqft", "median")).reset_index()
d = sp.merge(rp, on=["area_id", "year"])
d = d[(d["sales"] >= 30) & (d["rent_contracts"] >= 30)].copy()
d["yield_pct"] = 100 * d["rent_per_sqft"] / d["price_per_sqft"]
d["area"] = d["area_id"].map(names)
d["main_community"] = d["area_id"].map(label)
d.round(1).to_csv(base + "data/clean/dashboard_area_year.csv", index=False)
print("dashboard_area_year.csv:", len(d), "rows,", d["area_id"].nunique(), "areas")

sc = pd.read_csv(base + "data/clean/area_scores.csv", index_col=0)
sc["main_community"] = sc.index.map(label)
sc.index.name = "area_id"
sc.reset_index().to_csv(base + "data/clean/dashboard_area_scores.csv", index=False)
print("dashboard_area_scores.csv:", len(sc), "areas")

print("\nOfficial area name  ->  most common community/project name")
print(sc[["area", "main_community"]].head(15).to_string(index=False))
