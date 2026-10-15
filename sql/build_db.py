import os, sqlite3
import pandas as pd

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/")
conn = sqlite3.connect(base + "data/clean/dubai_property.db")

for table, file in [("sales", "sales_clean.csv"), ("rent", "rent_clean.csv")]:
    df = pd.read_csv(base + "data/clean/" + file)
    df.to_sql(table, conn, if_exists="replace", index=False)
    print(table, "loaded:", len(df), "rows")

conn.execute("CREATE INDEX idx_sales_area ON sales(area_id)")
conn.execute("CREATE INDEX idx_rent_area ON rent(area_id)")
conn.commit()
conn.close()
print("DONE")
