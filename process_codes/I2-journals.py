# -*- coding: utf-8 -*-
import os
import re
import glob
from typing import List, Optional
from collections import Counter
import pandas as pd
from pathlib import Path

REV_Q_MAP = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Unranked"}

TITLE_CANDIDATES = ["Title", "Journal", "Source title", "Journal Title", "Source Title"]
QUARTILE_CANDIDATES = ["SJR Best Quartile", "Best Quartile", "Quartile", "Quartile 2023", "Q"]
ISSN_CANDIDATES = ["ISSN", "Issn", "ISSN Print", "ISSN (print)", "ISSN (Print)", "ISSN/eISSN", "E-ISSN", "eISSN", "e-ISSN"]

FIELDS_ALLOWED = {"chemistry", "pharmacology", "physics", "bma"}

# ========= 基础函数 =========
def norm_text(s: str) -> str:
    if pd.isna(s): return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def norm_issn(s: str) -> str:
    if pd.isna(s): return ""
    s = str(s).upper()
    s = re.sub(r"[^0-9X]", "", s)
    return s

def standardize_issn(s: str) -> str:
    s = norm_issn(s)
    return s.zfill(8) if s else ""

def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in cols:
            return cols[name.lower()]
    return None

def parse_quartile_cell(x) -> Optional[str]:
    if pd.isna(x): return None
    s = str(x).strip().upper()
    if s in {"Q1", "Q2", "Q3", "Q4"}:
        return s
    if s in {"-", "UNRANKED"}:
        return "Unranked"
    return None

# ========= SCImago 处理 =========
def read_scimago_file(path: str, year: int, field: Optional[str]=None) -> pd.DataFrame:
    df = pd.read_excel(path)
    title_col = find_column(df, TITLE_CANDIDATES)
    quart_col = find_column(df, QUARTILE_CANDIDATES)
    issn_col  = find_column(df, ISSN_CANDIDATES)
    if quart_col is None:
        raise ValueError(f"[{path}] Could not find quartile column. Columns: {list(df.columns)}")
    
    expanded_rows = []
    for _, row in df.iterrows():
        issns = str(row[issn_col]).split(",") if issn_col else [""]
        for issn in issns:
            cleaned = norm_issn(issn)
            padded = cleaned.zfill(8) if cleaned else ""
            expanded_rows.append({
                "quartile": parse_quartile_cell(row[quart_col]),
                "journal_norm": norm_text(row[title_col]) if title_col is not None else "",
                "issn_clean": padded,
                "year": year,
                "field": str(field).strip().lower() if field else ""
            })
    return pd.DataFrame(expanded_rows)

def case_insensitive_globs(scimago_dir: str) -> List[str]:
    patterns = [
        os.path.join(scimago_dir, "scimago-*.xls"),
        os.path.join(scimago_dir, "scimago-*.xlsx"),
    ]
    matched = set()
    for pat in patterns:
        matched.update(glob.glob(pat))
    return sorted(matched)

def build_scimago_index(scimago_dir: str, fields: List[str]) -> pd.DataFrame:
    matched = case_insensitive_globs(scimago_dir)
    rows = []
    for p in matched:
        base = os.path.basename(p)
        m = re.match(r"scimago-(\d{4})-(.+?)\.(?:xlsx|xls)$", base, flags=re.IGNORECASE)
        if not m:
            continue
        year = int(m.group(1))
        file_field = m.group(2).strip()
        if fields:
            ok = any(file_field.lower() == f.lower() for f in fields)
            if not ok:
                continue
        try:
            df = read_scimago_file(p, year, field=file_field)
            rows.append(df)
        except Exception:
            continue
    if not rows:
        raise RuntimeError("No SCImago files loaded.")
    full = pd.concat(rows, ignore_index=True)
    full["field"] = full["field"].astype(str).str.strip().str.lower()
    full = full[full["field"].isin(FIELDS_ALLOWED)]
    full = full.drop_duplicates(subset=["issn_clean", "journal_norm", "year", "field", "quartile"])
    return full

# ========= Quartile helpers =========
def quartile_mode_excluding_missing(values: List[str]) -> int:
    q_to_num = {"Q1":1, "Q2":2, "Q3":3, "Q4":4, "Unranked":5}
    kept = [q_to_num[v] for v in values if v in q_to_num]
    if not kept:
        return 5
    counts = Counter(kept)
    maxf = max(counts.values())
    cands = [k for k, v in counts.items() if v == maxf]
    return min(cands)

def quartile_avg_round_excluding_missing(values: List[str]) -> int:
    q_to_num = {"Q1":1, "Q2":2, "Q3":3, "Q4":4, "Unranked":5}
    nums = [q_to_num[v] for v in values if v in q_to_num]
    if not nums:
        return 5
    return max(1, min(5, int(round(sum(nums)/len(nums)))))

# ========= Attach quartiles =========
def attach_quartiles_for_window_title(
    papers: pd.DataFrame,
    scimago_index: pd.DataFrame,
    fixed_pub_year: Optional[int] = None,
    journal_col_papers: str = "journal",
    field: Optional[str] = None,
    out_mode_col: str = "quartile_mode_15y",
    out_avg_col: str = "quartile_avg_round_15y",
) -> pd.DataFrame:

    df = papers.copy()
    df["journal_norm"] = df[journal_col_papers].map(norm_text) if journal_col_papers in df.columns else ""
    df["issn_clean"] = df["issn_clean"].map(standardize_issn) if "issn_clean" in df.columns else ""

    if fixed_pub_year is not None:
        df["_pub_year_for_window"] = int(fixed_pub_year)
    else:
        if "pub_year" not in df.columns:
            raise ValueError("No 'pub_year' column and no fixed_pub_year provided.")
        df["_pub_year_for_window"] = df["pub_year"].astype(int)

    mode_list, avg_list = [], []

    for _, row in df.iterrows():
        pub_y = int(row["_pub_year_for_window"])
        y1, y2 = pub_y + 1, pub_y + 15
        pool = scimago_index[(scimago_index["year"] >= y1) & (scimago_index["year"] <= y2)]
        if field:
            pool = pool[pool["field"] == field]

        issn_val = standardize_issn(row.get("issn_clean", ""))
        jour_val = row["journal_norm"]

        if issn_val and issn_val in pool["issn_clean"].values:
            vals = pool.loc[pool["issn_clean"] == issn_val, "quartile"].tolist()
        else:
            vals = pool.loc[pool["journal_norm"] == jour_val, "quartile"].tolist()

        mode_list.append(quartile_mode_excluding_missing(vals))
        avg_list.append(quartile_avg_round_excluding_missing(vals))

    df[out_mode_col] = mode_list
    df[out_avg_col] = avg_list
    df[out_mode_col + "_label"] = df[out_mode_col].map(REV_Q_MAP)
    df[out_avg_col + "_label"] = df[out_avg_col].map(REV_Q_MAP)
    df.drop(columns=["_pub_year_for_window"], inplace=True, errors="ignore")
    return df


# ---------------------------- 主程序入口 ----------------------------
if __name__ == "__main__":
    BASE = Path(__file__).resolve().parent.parent.parent
    BASE_DIR = BASE / "Disruptiveness-novelty"
    SCIMAGO_DIR = os.path.join(BASE_DIR, "journalranks")
    TOP5_DIR = os.path.join(BASE_DIR, "results", "top5")

    FIELDS = ["chemistry", "pharmacology", "physics", "bma"]

    INPUTS = []
    for fname in os.listdir(TOP5_DIR):
        if fname.endswith("_top5_sjr.csv"):
            year_field = fname.split("_")[0]  # e.g., 1999BMA
            year = int(year_field[:4])
            field = year_field[4:].lower()
            in_path = os.path.join(TOP5_DIR, fname)
            out_path = os.path.join(TOP5_DIR, f"{year}{field}_top5_with_15y_quartiles.csv")
            INPUTS.append((in_path, out_path, year))

    JOURNAL_COL_PAPERS = "journal"

    scimago_idx = build_scimago_index(SCIMAGO_DIR, FIELDS)
    # print(">>> SJR索引样本:")
    # print(scimago_idx[["issn_clean", "journal_norm", "year", "quartile"]].dropna().head(10))

    for in_path, out_path, fixed_pub_y in INPUTS:
        if not os.path.exists(in_path):
            print(f"Skip (missing): {in_path}")
            continue
        papers = pd.read_csv(in_path)
        inferred = next((f for f in FIELDS if f in in_path.lower()), None)
        out_df = attach_quartiles_for_window_title(
            papers, scimago_idx, fixed_pub_year=fixed_pub_y,
            journal_col_papers=JOURNAL_COL_PAPERS,
            field=inferred,
        )
        out_df.to_csv(out_path, index=False)
        print(f"Wrote: {out_path}")
