import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
works_file = BASE_DIR / "Disruptiveness-novelty/datasets/openalex-references.parquet"
BASE_IDS_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")          
BASE_MAPPING_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results") 
BASE_EDGES_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results") 

for d in [BASE_IDS_DIR, BASE_MAPPING_DIR, BASE_EDGES_DIR]:
    os.makedirs(d, exist_ok=True)

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

year_windows = {
    1999: (2000, 2014),
    2004: (2005, 2019),
    2009: (2010, 2024)
}

for field in fields:
    for year in years:

        target_id_file = f"{BASE_IDS_DIR}/{year}{field}_focal+reference_ids.txt"
        if not os.path.exists(target_id_file):
            continue

        output_file = f"{BASE_EDGES_DIR}/{year}{field}_citing_edges.csv"

        with open(target_id_file, "r") as f:
            target_ids = set(line.strip() for line in f if line.strip())

        START_YEAR, END_YEAR = year_windows[year]

        reader = pq.ParquetFile(works_file)
        edges = []

        for i in tqdm(range(reader.num_row_groups), desc=f"{year}-{field}"):
            table = reader.read_row_group(i, columns=["id", "publication_date", "referenced_works"])
            df = table.to_pandas()

            df = df[df["publication_date"].notnull()]
            df["publication_year"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.year
            df = df[(df["publication_year"] >= START_YEAR) & (df["publication_year"] <= END_YEAR)]

            for _, row in df.iterrows():
                refs = row["referenced_works"]
                if isinstance(refs, (list, np.ndarray)):
                    for cited_id in refs:
                        if cited_id in target_ids:
                            edges.append((row["id"], row["publication_date"], cited_id))

        df_edges = pd.DataFrame(edges, columns=["citing_id", "citing_pub_date", "cited_id"])
        df_edges.to_csv(output_file, index=False)
