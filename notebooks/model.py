import os, sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/")
conn = sqlite3.connect(base + "data/clean/dubai_property.db")
df = pd.read_sql("""SELECT area_id, area_name_en, instance_date, area_sqft,
                    price_per_sqft, rooms_en, reg_type_en
                    FROM sales WHERE property_sub_type_en = 'Flat'""",
                 conn, parse_dates=["instance_date"])
conn.close()

# ---- build features ----
df["month_idx"] = (df["instance_date"].dt.year - 2023) * 12 + df["instance_date"].dt.month
top = df["area_id"].value_counts().head(150).index
df["area_code"] = pd.factorize(np.where(df["area_id"].isin(top), df["area_id"], -1))[0]
df["rooms_code"] = pd.factorize(df["rooms_en"].fillna("Unknown"))[0]
df["reg_code"] = pd.factorize(df["reg_type_en"].fillna("Unknown"))[0]

cols = ["area_code", "rooms_code", "reg_code", "area_sqft", "month_idx"]
X = df[cols]
y = np.log(df["price_per_sqft"])
is_cat = [True, True, True, False, False]
print("Flats used:", len(df))

# ---- train and test ----
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
model = HistGradientBoostingRegressor(categorical_features=is_cat,
                                      max_iter=300, random_state=42)
model.fit(X_tr, y_tr)
pred = np.exp(model.predict(X_te))
actual = np.exp(y_te)

naive = np.exp(y_tr).median()
print("\nNaive guess (same price for every flat): typical error",
      round(100 * np.median(np.abs(naive - actual) / actual), 1), "%")
print("Our model: typical error",
      round(100 * np.median(np.abs(pred - actual) / actual), 1), "%")
print("R2 (log price):", round(r2_score(y_te, np.log(pred)), 3))

# ---- what drives price? ----
idx = X_te.sample(min(20000, len(X_te)), random_state=1).index
imp = permutation_importance(model, X_te.loc[idx], y_te.loc[idx],
                             n_repeats=3, random_state=0, scoring="r2")
names = {"area_code": "Area", "rooms_code": "Bedrooms", "reg_code": "Off-plan vs existing",
         "area_sqft": "Size (sqft)", "month_idx": "Date (market timing)"}
print("\nWhat drives price per sqft (higher = more important):")
for i in np.argsort(-imp.importances_mean):
    print("  ", names[cols[i]], round(imp.importances_mean[i], 3))

# ---- flag unusual deals (out-of-sample predictions) ----
oof = cross_val_predict(model, X, y, cv=5)
df["fair_psf"] = np.exp(oof)
df["gap_pct"] = 100 * (df["price_per_sqft"] / df["fair_psf"] - 1)
recent = df[df["instance_date"] >= "2026-01-01"]
print("\n2026 flat sales:", len(recent))
print("  more than 25% below model estimate:", int((recent["gap_pct"] <= -25).sum()))
print("  more than 25% above model estimate:", int((recent["gap_pct"] >= 25).sum()))

out = recent[["area_name_en", "instance_date", "area_sqft", "price_per_sqft",
              "fair_psf", "gap_pct"]].round(1)
out.sort_values("gap_pct").to_csv(base + "data/clean/deal_flags_2026.csv", index=False)
print("\nSaved data/clean/deal_flags_2026.csv")
