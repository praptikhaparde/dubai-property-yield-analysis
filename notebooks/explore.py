import os
import pandas as pd

raw = os.path.expanduser("~/Desktop/dubai-property-fair-value/data/raw/")

# RENTS
rent = pd.read_csv(
    raw + "rent_contracts_2026-10-07_18-06-59_0001.csv",
    usecols=["area_id", "area_name_en", "annual_amount", "actual_area",
             "contract_start_date", "ejari_property_type_en"],
)
rent["contract_start_date"] = pd.to_datetime(rent["contract_start_date"], errors="coerce")
print("RENTS rows:", len(rent))
print("Rent dates:", rent["contract_start_date"].min(), "to", rent["contract_start_date"].max())
print(rent["ejari_property_type_en"].value_counts().head(5))

# SALES
sales = pd.read_csv(
    raw + "transactions_2026-10-07_17-55-58_0001.csv",
    usecols=["area_id", "area_name_en", "actual_worth", "procedure_area",
             "instance_date", "trans_group_en", "property_type_en"],
)
sales["instance_date"] = pd.to_datetime(sales["instance_date"], errors="coerce")
print("\nSALES rows:", len(sales))
print("Sales dates:", sales["instance_date"].min(), "to", sales["instance_date"].max())
print(sales["trans_group_en"].value_counts())
