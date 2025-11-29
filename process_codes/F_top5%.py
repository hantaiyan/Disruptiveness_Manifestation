# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

BASE_MAPPING_DIR = BASE_DIR / "Disruptiveness-novelty" / "results"
BASE_OUT = BASE_DIR / "Disruptiveness-novelty" / "results" / "top5"
BASE_OUT.mkdir(parents=True, exist_ok=True)

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

def process_top5(orig_path, research_path):
    df_all = pd.read_csv(orig_path)

    di_cols = [
        col for col in df_all.columns
        if col.startswith("DI_y") and not col.endswith("_top5") and int(col.split("_")[1][1:]) >= 3
    ]

    thresholds = {col: df_all[col].quantile(0.95) for col in di_cols}

    for col in di_cols:
        df_all[col + "_top5"] = df_all[col] >= thresholds[col]

    top5_flags = df_all[[col + "_top5" for col in di_cols]]
    df_all["years_in_top5"] = top5_flags.sum(axis=1)
    df_all["first_year_top5"] = top5_flags.apply(lambda row: row.idxmax() if row.any() else None, axis=1)
    df_all["last_year_top5"] = top5_flags.apply(lambda row: row[::-1].idxmax() if row.any() else None, axis=1)

    research_data = df_all[df_all["years_in_top5"] > 0].copy()

    research_data.to_csv(research_path, index=False)


for year in years:
    for field in fields:

        orig_path = BASE_MAPPING_DIR / f"{year}{field}_focal_DI_y1_to_y15.csv"

        if not orig_path.exists():
            continue

        research_path = BASE_OUT / f"{year}{field}_focal_DI_top5_research_sample.csv"

        try:
            process_top5(orig_path, research_path)
        except Exception as e:
            print(f"出错：{year}-{field} {e}")
