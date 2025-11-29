# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
import pyarrow.dataset as ds
import os
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE = BASE_DIR / "Disruptiveness-novelty" / "results" / "top5"
BASE.mkdir(parents=True, exist_ok=True)

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

for year in years:
    for field in fields:

        in_path = f"{BASE}/{year}{field}_top5_focal_authors_with_prior_counts.csv"
        out_path = f"{BASE}/{year}{field}_top5_full_prior_stats.csv"

        if not os.path.exists(in_path):
            print("Not found")
            continue

        df = pd.read_csv(in_path)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"work_id": "focal_id"})  

        prior_col = [c for c in df.columns if c.startswith("prior_pubs_before_")]
        if len(prior_col) != 1:
            print("No data")
            continue
        prior_col = prior_col[0]

        first_authors = df[df['author_position'] == 'first'][['focal_id', prior_col]]
        first_authors_agg = first_authors.groupby('focal_id')[prior_col].mean().reset_index()
        first_authors_agg.rename(columns={prior_col: 'first_author_prior'}, inplace=True)

        df_unique = df.drop_duplicates(subset=["focal_id", "author_id"])
        author_avg = df_unique.groupby('focal_id')[prior_col].mean().reset_index()
        author_avg.rename(columns={prior_col: 'avg_all_authors_prior'}, inplace=True)

        author_count = df_unique.groupby('focal_id')['author_id'].count().reset_index()
        author_count.rename(columns={'author_id': 'author_count'}, inplace=True)

        all_ids = df[['focal_id']].drop_duplicates()
        merged = (all_ids
                  .merge(first_authors_agg, on='focal_id', how='left')
                  .merge(author_avg, on='focal_id', how='left')
                  .merge(author_count, on='focal_id', how='left'))

        merged.to_csv(out_path, index=False)
