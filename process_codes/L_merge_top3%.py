# -*- coding: utf-8 -*-
import pandas as pd
import os
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent.parent.parent
BASE_DIR = BASE / "Disruptiveness-novelty"
OUT_PATH = BASE_DIR / "data" / "all-top3.dta"
os.makedirs(OUT_PATH.parent, exist_ok=True)

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

def select_AC(row):
    delay = int(row["delay_year"])
    year = 3 + delay
    A_col = f"A_y{year}"
    C_col = f"C_y{year}"

    A_val = row[A_col] if A_col in row else None
    C_val = row[C_col] if C_col in row else None
    return pd.Series({"A_dynamic": A_val, "C_dynamic": C_val})

def load_and_merge_data(base_dir: Path, year: int, field: str) -> pd.DataFrame:

    word_path    = base_dir / "results" / "top5" / f"{year}{field}_focal_paper_textual_metrics_with_focalid.csv"
    delay_path   = base_dir / "results" / "top3" / f"{year}{field}_focal_top3_delay_years.csv"
    prior_path   = base_dir / "results" / "top5" / f"{year}{field}_top5_full_prior_stats.csv"
    team_path    = base_dir / "results" / "top5" / f"{year}{field}_top5_focal_author_counts.csv"
    journal_path = base_dir / "results" / "top5" / f"{year}{field}_top5_focal_with_quartiledata.csv"
    ij_path = base_dir / "results" / f"{year}{field}_A_C_foreign_ratio_cumulative.csv"
    AC_path = base_dir / "results" / "top5" / f"{year}{field}_focal_DI_top5_research_sample.csv"
    collaboration_path = base_dir / "results" / "top5" / f"{year}{field}_top5_focal_international.csv"
    


    try:
        word_df = pd.read_csv(word_path)[["focal_id", "new_phrase_comb", "n_phrases", "new_phrase", "new_word_comb"]]
        word_df["novelty"] = np.log1p(word_df["new_phrase_comb"])
        word_df.drop(columns=['new_phrase_comb'], inplace=True)

    except FileNotFoundError:
        word_df = pd.DataFrame()

    try:
        delay_df = pd.read_csv(delay_path)
        delay_df.rename(columns={'delay_years_to_top3': 'delay_year'}, inplace=True)
    except FileNotFoundError:
        delay_df = pd.DataFrame()

    try:
        prior_df = pd.read_csv(prior_path)
    except FileNotFoundError:
        prior_df = pd.DataFrame()

    try:
        team_df = pd.read_csv(team_path)
    except FileNotFoundError:
        team_df = pd.DataFrame()

    try:
        journal_df = pd.read_csv(journal_path)[["focal_id", "quartile_avg_round_15y_bin_Q1", "quartile_avg_round_15y_ord_1to5", "quartile_avg_round_15y_bin_Q12"]]
    except FileNotFoundError:
        journal_df = pd.DataFrame()

    try:
        ij_df = pd.read_csv(ij_path)
    except FileNotFoundError:
        ij_df = pd.DataFrame()

    try:
        AC_df = pd.read_csv(AC_path)
        cols_base = ["focal_id"]
        AC_df = AC_df[[c for c in AC_df.columns if c in cols_base or c.startswith(("A_y", "C_y"))]]
    except FileNotFoundError:
        AC_df = pd.DataFrame()

    try:
        collaboration_df = pd.read_csv(collaboration_path)[['work_id', 'is_international']]
        collaboration_df.rename(columns={'work_id': 'focal_id'}, inplace=True)
    except FileNotFoundError:
        collaboration_df = pd.DataFrame()

    df = delay_df
    for sub_df in [word_df, prior_df, team_df, journal_df, collaboration_df, AC_df, ij_df]:
        if not sub_df.empty:
            df = df.merge(sub_df, on="focal_id", how="left")

    df["year"] = year
    df["field"] = field

    df[["A_dynamic", "C_dynamic"]] = df.apply(select_AC, axis=1)
    df.rename(columns={"A_dynamic":"Ni_dynamic"},inplace=True)
    df.rename(columns={"C_dynamic":"Nj_dynamic"},inplace=True)
    df.rename(columns={"A_cum_foreign_ratio":"Ni_foreign_ratio"},inplace=True)
    df.rename(columns={"C_cum_foreign_ratio":"Nj_foreign_ratio"},inplace=True)
    df['citation_dynamic'] = df['Ni_dynamic'] + df['Nj_dynamic']
    cols_to_drop = [col for col in df.columns if col.startswith('A_y') or col.startswith('C_y')]
    df.drop(columns=cols_to_drop, inplace=True)
    df.rename(columns={"first_author_prior":"first_author_productivity"},inplace=True)
    df.rename(columns={"avg_all_authors_prior":"team_productivity"},inplace=True)
    df.rename(columns={"is_international":"inter_coauthorship"},inplace=True)
    df.rename(columns={"quartile_avg_round_15y_bin_Q1":"journal_tier"},inplace=True)
    df.rename(columns={"quartile_avg_round_15y_bin_Q12":"journal_tier_rc"},inplace=True)
    df.rename(columns={'quartile_avg_round_15y_ord_1to5':"journal_tier_orig5"}, inplace=True)

    return df


merged_all = []
for year in years:
    for field in fields:
        df = load_and_merge_data(BASE_DIR, year, field)
        if not df.empty:
            merged_all.append(df)

merged_all = pd.concat(merged_all, ignore_index=True)

merged_all["field"] = merged_all["field"].str.lower().map({
    "chemistry": 1,
    "pharmacology": 2,
    "physics": 3,
    "bma": 4
})


merged_all.to_stata(OUT_PATH, write_index=False)
