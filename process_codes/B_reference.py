import pyarrow.dataset as ds
import pandas as pd
import csv
import numpy as np
from tqdm import tqdm
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "Disruptiveness-novelty"
BASE_DIR.mkdir(parents=True, exist_ok=True)

REFERENCES_PARQUET = BASE_DIR / "datasets" / "openalex-references.parquet"

BASE_FOCAL_DIR = BASE_DIR / "results"

BASE_OUTPUT_DIR = BASE_DIR / "results"
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

dataset = ds.dataset(REFERENCES_PARQUET, format="parquet")
scanner = dataset.scanner(columns=['id', 'referenced_works'])

for field in fields:
    for year in years:

        focal_csv_path = BASE_FOCAL_DIR / f"{year}{field}_ids_from_primary.csv"
        if not focal_csv_path.exists():
            continue

        output_txt_path = BASE_OUTPUT_DIR / f"{year}{field}_focal+reference_ids.txt"
        output_mapping_csv = BASE_OUTPUT_DIR / f"{year}{field}_focal_reference_mapping.csv"

        focal_ids = pd.read_csv(focal_csv_path)['id'].astype(str).tolist()
        focal_ids_set = set(focal_ids)

        with open(output_mapping_csv, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['focal_id', 'reference_id'])

            all_ids_set = set()
            match_count = 0
            ref_written_count = 0
            ref_empty_count = 0

            with tqdm(total=100000, desc=f"{year}-{field}", unit="条") as pbar:
                for batch in scanner.to_batches():
                    df = batch.to_pandas()
                    for _, row in df.iterrows():
                        pbar.update(1)

                        focal_id = row['id']
                        if focal_id not in focal_ids_set:
                            continue

                        references = row['referenced_works']

                        if not isinstance(references, (list, np.ndarray)) or len(references) == 0:
                            ref_empty_count += 1
                            continue

                        match_count += 1
                        for ref_id in references:
                            if ref_id:
                                csv_writer.writerow([focal_id, ref_id])
                                all_ids_set.add(focal_id)
                                all_ids_set.add(ref_id)
                                ref_written_count += 1

        with open(output_txt_path, 'w') as f_txt:
            for _id in sorted(all_ids_set):
                f_txt.write(_id + '\n')
