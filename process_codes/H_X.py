# -*- coding: utf-8 -*-
import pandas as pd
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
BASE_DIR = BASE / "Disruptiveness-novelty"


BASE_DELAY = BASE_DIR / "results" / "top5"   
TEXTUAL_FILE = BASE_DIR / "datasets" / "papers_textual_metrics.csv"
BASE_OUT = BASE_DIR / "results" / "top5"
BASE_OUT.mkdir(parents=True, exist_ok=True)

years = [1999, 2004, 2009]
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]

textual_df = pd.read_csv(TEXTUAL_FILE)
textual_df["PaperID"] = textual_df["PaperID"].astype(str)

for year in years:
    for field in fields:
        in_path = BASE_DELAY / f"{year}{field}_focal_top5_delay_years.csv"
        out_path = BASE_OUT / f"{year}{field}_focal_paper_textual_metrics_with_focalid.csv"

        if not in_path.exists():
            continue

        focal_df = pd.read_csv(in_path)

        focal_df["pure_id"] = focal_df["focal_id"].astype(str).str.extract(r"(W\d+)$")
        focal_ids = set(focal_df["pure_id"].dropna())

        focal_textual_df = textual_df[textual_df["PaperID"].isin(focal_ids)].copy()

        focal_textual_df = focal_textual_df.merge(
            focal_df[["focal_id", "pure_id"]],
            left_on="PaperID", right_on="pure_id",
            how="left"
        )

        mask_na = focal_textual_df["focal_id"].isna()
        if mask_na.any():
            focal_textual_df.loc[mask_na, "focal_id"] = (
                "https://openalex.org/" + focal_textual_df.loc[mask_na, "PaperID"].astype(str)
            )

        focal_textual_df = focal_textual_df.drop(columns=["PaperID", "pure_id"])

        focal_textual_df.to_csv(out_path, index=False)
