import os
import gzip
import json
import argparse
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# ========== Path ==========
INPUT_FOLDER = '/Users/zhaoxinhang/openalex-snapshot/data/works'
CHUNK_FOLDER = '/Users/zhaoxinhang/openalex-primary-parquet/chunks'
FINAL_OUTPUT = '/Users/zhaoxinhang/openalex-primary.parquet'

os.makedirs(CHUNK_FOLDER, exist_ok=True)

# ========== Parquet schema ==========
schema = pa.schema([
    ("id", pa.string()),
    ("publication_date", pa.string()),
    ("source_id", pa.string()),
    ("source_type", pa.string()),
    ("source_name", pa.string()),
    ("issn_l", pa.string())
])

BATCH_SIZE = 10000
ALLOWED_FIELDS = set(schema.names)

# ========== Single .gz file processing ==========
def extract_primary_streaming(gz_file):
    input_path = os.path.join(INPUT_FOLDER, gz_file)
    output_path = os.path.join(CHUNK_FOLDER, gz_file.replace('.gz', '.parquet'))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    writer = None
    batch = []

    try:
        with gzip.open(input_path, 'rt', encoding='utf-8') as fin:
            for line in fin:
                work = json.loads(line)
                paper_id = work.get("id")
                publication_date = work.get("publication_date")

                # 提取 primary_location.source
                primary = work.get("primary_location")
                if not primary:
                    continue
                psource = primary.get("source")
                if not psource:
                    continue

                if psource:
                    batch.append({
                        "id": paper_id,
                        "publication_date": publication_date,
                        "source_id": psource.get("id"),
                        "source_type": psource.get("type"),
                        "source_name": psource.get("display_name"),
                        "issn_l": psource.get("issn_l")
                    })

                if len(batch) >= BATCH_SIZE:
                    table = pa.Table.from_pylist(batch)
                    table = table.select([f for f in table.column_names if f in ALLOWED_FIELDS])
                    table = table.cast(schema)
                    if writer is None:
                        writer = pq.ParquetWriter(output_path, schema=schema)
                    writer.write_table(table)
                    batch = []

        if batch:
            table = pa.Table.from_pylist(batch)
            table = table.select([f for f in table.column_names if f in ALLOWED_FIELDS])
            table = table.cast(schema)
            if writer is None:
                writer = pq.ParquetWriter(output_path, schema=schema)
            writer.write_table(table)

    except Exception as e:
        print(f"fail {gz_file} ：{e}")
    finally:
        if writer:
            writer.close()

# ========== Merging all Parquet ==========
def merge_parquet_chunks():
    parquet_files = []
    for root, _, files in os.walk(CHUNK_FOLDER):
        for fname in files:
            if fname.endswith('.parquet'):
                parquet_files.append(os.path.join(root, fname))

    print(f"found {len(parquet_files)}  parquet files waiting for merging")

    if not parquet_files:
        print("chunk not found")
        return

    with pq.ParquetWriter(FINAL_OUTPUT, schema=schema) as writer:
        for fpath in tqdm(sorted(parquet_files)):
            try:
                table = pq.read_table(fpath)
                table = table.select([f for f in table.column_names if f in ALLOWED_FIELDS])
                table = table.cast(schema)
                writer.write_table(table)
            except Exception as e:
                print(f"Fail to merge {fpath}：{e}")
    print(f"Merge finished：{FINAL_OUTPUT}")

# ========== main ==========
def main(args):
    if not args.merge_only:
        gz_files = [
            os.path.join(root, fname)[len(INPUT_FOLDER)+1:]
            for root, _, files in os.walk(INPUT_FOLDER)
            for fname in files if fname.endswith(".gz")
        ]
        print(f"Found {len(gz_files)}  .gz files，start extracting primary_location...")

        with Pool(processes=max(cpu_count() // 2, 1)) as pool:
            list(tqdm(pool.imap_unordered(extract_primary_streaming, gz_files), total=len(gz_files)))

    if not args.extract_only:
        merge_parquet_chunks()

# ========== CLI ==========
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract and merge OpenAlex primary_location")
    parser.add_argument('--extract-only', action='store_true', help="Only extracting")
    parser.add_argument('--merge-only', action='store_true', help="Only merging")
    args = parser.parse_args()
    main(args)
