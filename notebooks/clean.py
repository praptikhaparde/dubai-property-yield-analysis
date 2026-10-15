import os
import pandas as pd

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/")
raw, out = base + "data/raw/", base + "data/clean/"
SQM_TO_SQFT = 10.7639
START, END = "2023-01-01", "2026-09-30"

def trim(df, col, by):
    lo = df.groupby(by)[col].transform(lambda s: s.quantile(0.01))
    hi = df.groupby(by)[col].transform(lambda s: s.quantile(0.99))
    return df[(df[col] >= lo) & (df[col] <= hi)]

# ---------- RENTS ----------
r = pd.read_csv(raw + "rent_contracts_2026-10-07_18-06-59_0001.csv",
    usecols=["area_id", "area_name_en", "annual_amount", "actual_area",
             "contract_start_date", "ejari_property_type_en",
             "ejari_property_sub_type_en", "contract_reg_type_en"])
print("RENTS start:", len(r))
r["contract_start_date"] = pd.to_datetime(r["contract_start_date"], errors="coerce")
r = r[r["ejari_property_type_en"].isin(["Flat", "Villa"])]
print("  after Flat/Villa only:", len(r))
r = r[(r["contract_start_date"] >= START) & (r["contract_start_date"] <= END)]
print("  after date filter:", len(r))
r = r[(r["annual_amount"] > 0) & (r["actual_area"] > 0)]
r["area_sqft"] = r["actual_area"] * SQM_TO_SQFT
r = r[(r["area_sqft"] >= 150) & (r["area_sqft"] <= 20000)]
print("  after valid size/amount:", len(r))
r = r.drop_duplicates()
print("  after duplicates removed:", len(r))
r["rent_per_sqft"] = r["annual_amount"] / r["area_sqft"]
r = trim(r, "rent_per_sqft", "ejari_property_type_en")
print("  after outlier trim:", len(r))
r.to_csv(out + "rent_clean.csv", index=False)

# ---------- SALES ----------
s = pd.read_csv(raw + "transactions_2026-10-07_17-55-58_0001.csv",
    usecols=["area_id", "area_name_en", "actual_worth", "procedure_area",
             "instance_date", "trans_group_en", "property_sub_type_en",
             "property_usage_en", "reg_type_en", "rooms_en"])
print("\nSALES start:", len(s))
s = s[s["trans_group_en"] == "Sales"]
print("  after Sales only:", len(s))
s = s[(s["property_usage_en"] == "Residential") & (s["property_sub_type_en"].isin(["Flat", "Villa"]))]
print("  after residential Flat/Villa:", len(s))
s["instance_date"] = pd.to_datetime(s["instance_date"], errors="coerce")
s = s[(s["instance_date"] >= START) & (s["instance_date"] <= END)]
print("  after date filter:", len(s))
s = s[(s["actual_worth"] > 0) & (s["procedure_area"] > 0)]
s["area_sqft"] = s["procedure_area"] * SQM_TO_SQFT
s = s[(s["area_sqft"] >= 150) & (s["area_sqft"] <= 20000)]
print("  after valid size/price:", len(s))
s = s.drop_duplicates()
print("  after duplicates removed:", len(s))
s["price_per_sqft"] = s["actual_worth"] / s["area_sqft"]
s = trim(s, "price_per_sqft", "property_sub_type_en")
print("  after outlier trim:", len(s))
s.to_csv(out + "sales_clean.csv", index=False)

print("\nMedian AED per sqft (sales):\n", s.groupby("property_sub_type_en")["price_per_sqft"].median().round(0))
print("\nMedian annual AED per sqft (rent):\n", r.groupby("ejari_property_type_en")["rent_per_sqft"].median().round(1))
print("\nDONE. Files saved in data/clean/")
