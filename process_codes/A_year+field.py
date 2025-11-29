import pandas as pd
import sqlite3
import pyarrow.dataset as ds
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "Disruptiveness-novelty"
BASE_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_FILE = BASE_DIR / "datasets" / "openalex-arts.sqlite"
TABLE_NAME = "primary_source"
AUTHORS_PARQUET = BASE_DIR / "datasets" / "openalex-authors.parquet" #also can use sqlite
JOURNAL_DIR = BASE_DIR / "journalranks"


fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

def normalize_issn(raw):
    if not raw or not isinstance(raw, str):
        return None
    i = raw.strip().upper()
    i = i.replace(" ", "").replace("-", "").replace(";", ",").replace("/", ",").replace(".", "")
    if not all(c.isdigit() or c == "X" for c in i):
        return None
    if len(i) < 8:
        i = i.zfill(8)
    if len(i) == 8 and "-" not in i:
        i = i[:4] + "-" + i[4:]
    return i

authors_ds = ds.dataset(AUTHORS_PARQUET, format="parquet")

for field in fields:
    for year in years:
        ISSN_EXCEL_FILE = JOURNAL_DIR / f"scimago-{year}-{field}.xlsx"

        journal_info = pd.read_excel(ISSN_EXCEL_FILE)
        norm_issns = set()
        for issns in journal_info['Issn'].dropna():
            for part in str(issns).replace(";", ",").replace("/", ",").split(","):
                norm = normalize_issn(part)
                if norm:
                    norm_issns.add(norm)
                    
        if norm_issns:
            placeholders = ",".join(["?"] * len(norm_issns))
            query = f"""
            SELECT DISTINCT id, issn_l
            FROM "{TABLE_NAME}"
            WHERE issn_l IN ({placeholders})
              AND substr(publication_date, 1, 4) = ?
            """
            conn = sqlite3.connect(SQLITE_FILE)
            df_extra = pd.read_sql_query(query, conn, params=list(norm_issns) + [str(year)])
            conn.close()
        else:
            df_extra = pd.DataFrame(columns=["id", "issn_l"])


        extra_ids = set(df_extra["id"].astype(str))
        work_ids_with_authors = set()

        for batch in authors_ds.to_batches(columns=["work_id"]):
            bdf = batch.to_pandas()
            matched = bdf[bdf["work_id"].isin(extra_ids)]
            work_ids_with_authors.update(matched["work_id"].astype(str))

        df_extra_filtered = df_extra[df_extra["id"].astype(str).isin(work_ids_with_authors)]

        n_journals = df_extra_filtered["issn_l"].nunique()
        n_papers = len(df_extra_filtered)


        output_ids_file = BASE_DIR / f"{year}{field}_ids_from_primary.csv"
        df_extra_filtered[['id']].to_csv(output_ids_file, index=False)
        print(f"{year}-{field}: 已保存 focal ids 至 {output_ids_file}")
