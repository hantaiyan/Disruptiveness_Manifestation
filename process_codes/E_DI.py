# -*- coding: utf-8 -*-
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE_EDGES_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")
BASE_FILTERED_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")
BASE_DI_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")
os.makedirs(BASE_DI_DIR, exist_ok=True)

fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]


def compute_DI(year, field, low, high):

    mapping_path = f"{BASE_FILTERED_DIR}/{year}{field}_focal_reference_mapping_filtered.csv"
    edges_path = f"{BASE_EDGES_DIR}/{year}{field}_citing_edges.csv"
    if not os.path.exists(mapping_path) or not os.path.exists(edges_path):
        return None

    output_path = f"{BASE_DI_DIR}/{year}{field}_focal_DI_y{low}_to_y{high}.csv"

    f2r = pd.read_csv(mapping_path)
    focal_set = set(f2r["focal_id"])
    reference_set = set(f2r["reference_id"])

    ref_to_focal = defaultdict(set)
    for _, row in tqdm(f2r.iterrows(), total=len(f2r), desc="ref_to_focal"):
        ref_to_focal[row["reference_id"]].add(row["focal_id"])

    focal_to_refs = f2r.groupby("focal_id")["reference_id"].apply(set).to_dict()

    di_accum = defaultdict(lambda: defaultdict(lambda: {"A": 0, "B": 0, "C": 0}))

    chunk_iter = pd.read_csv(
        edges_path,
        parse_dates=["citing_pub_date"],
        chunksize=500_000
    )

    for chunk in tqdm(chunk_iter, desc=f"chunks-{year}-{field}"):
        chunk["citing_year"] = chunk["citing_pub_date"].dt.year
        chunk["year_diff"] = chunk["citing_year"] - year
        chunk = chunk[(chunk["year_diff"] >= low) & (chunk["year_diff"] <= high)]

        grouped = chunk.groupby("citing_id").agg({
            "year_diff": "first",  
            "cited_id": list
        }).reset_index()

        for _, row in grouped.iterrows(): 
            y = row["year_diff"]
            cited_ids = set(row["cited_id"])

            cited_focals = cited_ids & focal_set
            cited_refs = cited_ids & reference_set

            linked_focals = set(cited_focals)
            for ref in cited_refs:
                linked_focals.update(ref_to_focal.get(ref, set()))

            for focal in linked_focals:
                has_focal = focal in cited_focals
                has_ref = len(focal_to_refs.get(focal, set()) & cited_ids) > 0 

                if has_focal and has_ref:
                    di_accum[focal][y]["C"] += 1
                elif has_focal:
                    di_accum[focal][y]["A"] += 1
                elif has_ref:
                    di_accum[focal][y]["B"] += 1


    print("Finalizing output...")
    records = []
    for focal in tqdm(sorted(focal_set), desc=f"Output-{year}-{field}"):
        row = {"focal_id": focal}
        for y in range(low, high + 1):
            A = sum(di_accum[focal][yy]["A"] for yy in range(low, y + 1))
            B = sum(di_accum[focal][yy]["B"] for yy in range(low, y + 1))
            C = sum(di_accum[focal][yy]["C"] for yy in range(low, y + 1))

            total = A + B + C
            DI = (A - C) / total if total > 0 else None
            row[f"DI_y{y}"] = round(DI, 4) if DI is not None else None
            row[f"A_y{y}"] = A
            row[f"B_y{y}"] = B
            row[f"C_y{y}"] = C
        records.append(row)

    df_result = pd.DataFrame(records)
    df_result.to_csv(output_path, index=False)

    return output_path

def main():
    for year in years:
        for field in fields:
            compute_DI(year, field, 1, 15)


if __name__ == "__main__":
    main()
 
