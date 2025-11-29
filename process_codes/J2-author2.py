# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
import pyarrow.dataset as ds
import os
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE = BASE_DIR / "Disruptiveness-novelty" / "results" / "top5"
BASE.mkdir(parents=True, exist_ok=True)

AUTHORS_PARQUET = BASE_DIR / "Disruptiveness-novelty/datasets/openalex-authors.parquet"
REFERENCES_PARQUET = BASE_DIR / "Disruptiveness-novelty/datasets/openalex-references.parquet"

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

authors_ds = ds.dataset(AUTHORS_PARQUET, format="parquet")
refs_ds = ds.dataset(REFERENCES_PARQUET, format="parquet")

for year in years:
    for field in fields:

        in_path = f"{BASE}/{year}{field}_top5_focal_authors.parquet"
        if not os.path.exists(in_path):
            print("Not found")
            continue

        out_path = f"{BASE}/{year}{field}_top5_focal_authors_with_prior_counts.csv"

        focal_df = pd.read_parquet(in_path)
        if "author_id" not in focal_df.columns:
            print("No data")
            continue

        focal_author_ids = focal_df["author_id"].dropna().unique().tolist()
        focal_author_set = set(focal_author_ids)

        if len(focal_author_set) == 0:
            print("No data")
            continue

        author_to_works = defaultdict(set)
        for batch in authors_ds.to_batches(columns=["author_id", "work_id"]):
            df = batch.to_pandas()
            df = df[df["author_id"].isin(focal_author_set)]
            for _, row in df.iterrows():
                author_to_works[row["author_id"]].add(row["work_id"])

        all_work_ids = set(w for works in author_to_works.values() for w in works)
        work_to_year = {}
        for batch in refs_ds.to_batches(columns=["id", "publication_date"]):
            df = batch.to_pandas()
            df = df[df["id"].isin(all_work_ids)]
            df["year"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.year
            for _, row in df.iterrows():
                work_to_year[row["id"]] = row["year"]

        cutoff_year = year 
        author_prior_counts = {
            author: sum(1 for wid in works if work_to_year.get(wid, 9999) < cutoff_year)
            for author, works in author_to_works.items()
        }

        focal_df[f"prior_pubs_before_{year}"] = focal_df["author_id"].map(author_prior_counts)
        focal_df.to_csv(out_path, index=False)
