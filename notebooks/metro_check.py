import os
import pandas as pd

raw = os.path.expanduser("~/Desktop/dubai-property-fair-value/data/raw/")
s = pd.read_csv(raw + "transactions_2026-10-07_17-55-58_0001.csv",
    usecols=["area_id", "area_name_en", "actual_worth", "procedure_area", "instance_date",
             "trans_group_en", "property_sub_type_en", "property_usage_en",
             "reg_type_en", "nearest_metro_en"])
s = s[(s["trans_group_en"] == "Sales") & (s["property_usage_en"] == "Residential")
      & (s["property_sub_type_en"] == "Flat") & (s["reg_type_en"] == "Existing Properties")]
s["instance_date"] = pd.to_datetime(s["instance_date"], errors="coerce")
s = s[(s["instance_date"] >= "2023-01-01") & (s["instance_date"] <= "2026-09-30")]
s = s[(s["actual_worth"] > 0) & (s["procedure_area"] > 0)]
s["sqft"] = s["procedure_area"] * 10.7639
s = s[(s["sqft"] >= 150) & (s["sqft"] <= 20000)]
s["psf"] = s["actual_worth"] / s["sqft"]
s = s[(s["psf"] >= s["psf"].quantile(0.01)) & (s["psf"] <= s["psf"].quantile(0.99))]
s["has_metro"] = s["nearest_metro_en"].notna() & (s["nearest_metro_en"].astype(str).str.strip() != "")

print("Existing flat sales used:", len(s))
print("Share with a metro label:", round(100 * s["has_metro"].mean(), 1), "%")
print("Different stations named:", s.loc[s["has_metro"], "nearest_metro_en"].nunique())

print("\nMedian price per sqft: metro label vs blank (all Dubai)")
print(s.groupby("has_metro")["psf"].agg(["size", "median"]).round(0))

st = (s[s["has_metro"]].groupby("nearest_metro_en")["psf"]
      .agg(deals="size", median_psf="median").sort_values("deals", ascending=False).head(10))
print("\n10 stations with the most sales:")
print(st.round(0))

m = s.groupby(["area_id", "has_metro"])["psf"].agg(n="size", med="median").reset_index()
a = m[m["has_metro"]].set_index("area_id")
b = m[~m["has_metro"]].set_index("area_id")
j = a.join(b, lsuffix="_metro", rsuffix="_none", how="inner")
j = j[(j["n_metro"] >= 100) & (j["n_none"] >= 100)]
j["ratio"] = j["med_metro"] / j["med_none"]
print("\nWITHIN THE SAME AREA (areas with 100+ sales in both groups):", len(j))
if len(j) > 0:
    print("  Median price ratio, metro label vs blank:", round(j["ratio"].median(), 2))
    print("  Areas where metro-label flats cost more:", int((j["ratio"] > 1).sum()), "of", len(j))
