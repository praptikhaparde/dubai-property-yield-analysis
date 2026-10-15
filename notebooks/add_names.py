import os
import pandas as pd

base = os.path.expanduser("~/Desktop/dubai-property-fair-value/data/clean/")
friendly = {
    "Nadd Hessa": "Dubai Silicon Oasis",
    "Al Barsha South Fifth": "JVT (Jumeirah Village Triangle)",
    "Al Barsha South Fourth": "JVC (Jumeirah Village Circle)",
    "Al Barshaa South Third": "Arjan",
    "Al Hebiah Fourth": "Dubai Sports City",
    "Al Hebiah Third": "DAMAC Hills",
    "Al Yelayiss 2": "Town Square",
    "Al Warsan First": "International City",
    "Wadi Al Safa 5": "Dubai Land Residence Complex",
    "Wadi Al Safa 3": "Majan",
    "Madinat Al Mataar": "Dubai South",
    "Jabal Ali First": "Jabal Ali First (incl. Al Furjan)",
    "Me'Aisem First": "Dubai Production City (IMPZ)",
    "Al Thanyah Fifth": "Al Thanyah Fifth (incl. JLT)",
    "Al Thanyah Third": "Al Thanyah Third (incl. The Greens)",
    "Marsa Dubai": "Dubai Marina",
    "Burj Khalifa": "Downtown Dubai",
}
for f in ["dashboard_area_scores.csv", "dashboard_area_year.csv"]:
    d = pd.read_csv(base + f)
    d["display_name"] = d["area"].map(friendly).fillna(d["area"])
    d.to_csv(base + f.replace(".csv", "_final.csv"), index=False)
    print(f, "->", f.replace(".csv", "_final.csv"))

d = pd.read_csv(base + "dashboard_area_scores_final.csv")
print(d[["area", "display_name", "yield_pct", "growth_pct"]].round(1).to_string(index=False))
