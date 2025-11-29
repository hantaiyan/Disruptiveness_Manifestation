import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm

tqdm.pandas()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

BASE_MAPPING_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")
BASE_EDGES_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")
BASE_FILTERED_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")

for d in [BASE_MAPPING_DIR, BASE_EDGES_DIR, BASE_FILTERED_DIR]:
    os.makedirs(d, exist_ok=True)

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

for field in fields:
    for year in years:

        mapping_path = f"{BASE_MAPPING_DIR}/{year}{field}_focal_reference_mapping.csv"
        edges_path = f"{BASE_EDGES_DIR}/{year}{field}_citing_edges.csv"

        if not os.path.exists(mapping_path) or not os.path.exists(edges_path):
            continue

        output_path = f"{BASE_FILTERED_DIR}/{year}{field}_focal_reference_mapping_filtered.csv"

        df_map = pd.read_csv(mapping_path)

        df_map['reference_id'] = df_map['reference_id'].apply(
            lambda rid: rid if str(rid).startswith("https://openalex.org/") else "https://openalex.org/" + str(rid)
        )

        focal_ref_counts = df_map['focal_id'].value_counts()
        valid_focals_by_ref = set(focal_ref_counts[focal_ref_counts >= 5].index)

        df_edges = pd.read_csv(edges_path)
        focal_cited_counts = df_edges['cited_id'].value_counts()
        valid_focals_by_cited = set(focal_cited_counts[focal_cited_counts >= 5].index)

        valid_focals_final = valid_focals_by_ref & valid_focals_by_cited

        df_map_filtered = df_map[df_map['focal_id'].progress_apply(lambda x: x in valid_focals_final)]

        df_map_filtered.to_csv(output_path, index=False)
