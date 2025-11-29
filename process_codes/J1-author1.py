import pandas as pd
import pyarrow.dataset as ds
import pyarrow.compute as pc
import pyarrow as pa
import pyarrow.parquet as pq
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE = BASE_DIR / "Disruptiveness-novelty" / "results" / "top5"
BASE.mkdir(parents=True, exist_ok=True)

AUTHORS_PARQUET = BASE_DIR / "Disruptiveness-novelty/datasets/openalex-authors.parquet"
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]


authors_ds = ds.dataset(AUTHORS_PARQUET, format="parquet")

for year in years:
    for field in fields:

        top5_path = f"{BASE}/{year}{field}_focal_DI_top5_research_sample.csv"
        if not os.path.exists(top5_path):
            print("Not found")
            continue

        output_path = f"{BASE}/{year}{field}_top5_focal_authors.parquet"

        focal_df = pd.read_csv(top5_path)
        if "focal_id" not in focal_df.columns:
            print("no data")
            continue
        focal_ids = focal_df["focal_id"].astype(str).unique().tolist()

        if len(focal_ids) == 0:
            print("No data")
            continue

        focal_id_array = pa.array(focal_ids, type=pa.string())
        filter_expr = pc.is_in(ds.field("work_id"), value_set=focal_id_array)

        filtered_table = authors_ds.to_table(filter=filter_expr)

        pq.write_table(filtered_table, output_path)
