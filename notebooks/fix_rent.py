import os, sqlite3
import pandas as pd

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/")
SQM_TO_SQFT = 10.7639
START, END = "2023-01-01", "2026-09-30"

r = pd.read_csv(base + "data/raw/rent_contracts_2026-10-07_18-06-59_0001.csv",
    usecols=["area_id", "area_name_en", "annual_amount", "actual_area",
             "contract_start_date", "ejari_property_type_en",
             "ejari_property_sub_type_en", "contract_reg_type_en", "no_of_prop"])
print("RENTS start:", len(r))
r["contract_start_date"] = pd.to_datetime(r["contract_start_date"], errors="coerce")
r = r[r["ejari_property_type_en"].isin(["Flat", "Villa"])]
print("  after Flat/Villa only:", len(r))
r = r[(r["contract_start_date"] >= START) & (r["contract_start_date"] <= END)]
print("  after date filter:", len(r))
r = r[r["no_of_prop"] == 1]
print("  after single-property contracts only:", len(r))
r = r[(r["annual_amount"] > 0) & (r["actual_area"] > 0)]
r["area_sqft"] = r["actual_area"] * SQM_TO_SQFT
r = r[(r["area_sqft"] >= 150) & (r["area_sqft"] <= 20000)]
r = r.drop_duplicates()
print("  after valid size/amount and duplicates:", len(r))
r["rent_per_sqft"] = r["annual_amount"] / r["area_sqft"]
r = r[(r["rent_per_sqft"] >= 20) & (r["rent_per_sqft"] <= 250)]
print("  after rent per sqft between 20 and 250:", len(r))

r.to_csv(base + "data/clean/rent_clean.csv", index=False)
conn = sqlite3.connect(base + "data/clean/dubai_property.db")
r.to_sql("rent", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX idx_rent_area ON rent(area_id)")
conn.commit()
conn.close()
print("DONE. Rent table rebuilt.")
