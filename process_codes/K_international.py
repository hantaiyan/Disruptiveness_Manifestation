# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

BASE_DIR = Path("/Users/zhaoxinhang/Disruptiveness-novelty")
RESULTS_DIR = BASE_DIR / "results" / "top5"

years  = [1999, 2004, 2009]
fields = ["Chemistry", "Pharmacology", "Physics", "BMA"]

REQUIRED_COLS = {"work_id", "author_id", "institution_country"}

def clean_country(c):
    if pd.isna(c):
        return ""
    c = str(c).strip().upper()
    return "" if c in {"", "NAN", "NA", "NONE", "NULL"} else c

def compute_international_by_paper(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Lack essential columns: {missing}")

    df = df.copy()
    df["institution_country"] = df["institution_country"].map(clean_country)

    def agg_one(sub: pd.DataFrame) -> pd.Series:
        n_authors = sub["author_id"].nunique()
        if n_authors >= 2:
            countries = sorted({c for c in sub["institution_country"].tolist() if c})
            n_countries = len(countries)
            is_international = 1 if n_countries >= 2 else 0
        else:
            countries = []
            n_countries = 0
            is_international = 0

        return pd.Series({
            "n_authors": n_authors,
            "n_affiliations": len(sub),
            "n_countries": n_countries,
            "countries": ",".join(countries),
            "is_international": is_international
        })

    out = (
        df.groupby("work_id", as_index=False)
          .apply(agg_one)
          .reset_index(drop=True)
    )
    return out

def run_one(year: int, field: str):
    in_file  = RESULTS_DIR / f"{year}{field}_top5_focal_authors_with_prior_counts.csv"
    out_file = RESULTS_DIR / f"{year}{field}_top5_focal_international.csv"
    if not in_file.exists():
        print("Not found")
        return
    print(f"Processing: {in_file.name}")

    df = pd.read_csv(in_file)
    df.columns = [c.strip() for c in df.columns]  

    if "institution_country" not in df.columns:
        print("pass")
        return

    res = compute_international_by_paper(df)
    res.to_csv(out_file, index=False)
    print(f"→ Saved: {out_file.name} (rows={len(res)})")

if __name__ == "__main__":
    for y in years:
        for f in fields:
            try:
                run_one(y, f)
            except Exception as e:
                print("Fail")
