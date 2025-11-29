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
CHUNK_FOLDER = '/Users/zhaoxinhang/openalex-references-parquet/chunks'
FINAL_OUTPUT = '/Users/zhaoxinhang/openalex-references.parquet'

os.makedirs(CHUNK_FOLDER, exist_ok=True)

# ========== Parquet schema ==========
schema = pa.schema([
    ("id", pa.string()),
    ("publication_date", pa.string()),
    ("referenced_works", pa.list_(pa.string()))
])

BATCH_SIZE = 10000
ALLOWED_FIELDS = set(schema.names)

# ========== Single .gz processing ==========
def extract_references_streaming(gz_file):
    input_path = os.path.join(INPUT_FOLDER, gz_file)
    output_path = os.path.join(CHUNK_FOLDER, gz_file.replace('.gz', '.parquet'))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    writer = None
    batch = []

    try:
        with gzip.open(input_path, 'rt', encoding='utf-8') as fin:
            for line in fin:
                work = json.loads(line)
                paper_id = work.get('id')
                publication_date = work.get('publication_date')
                references = work.get('referenced_works', [])

                if paper_id and isinstance(references, list):
                    batch.append({
                        "id": paper_id,
                        "publication_date": publication_date,
                        "referenced_works": references
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
        print(f"Fail {gz_file} ：{e}")
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

    print(f"Found {len(parquet_files)} parquet files waiting for merging")

    if not parquet_files:
        print("Fail to find any chunk files")
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
    print(f"Complete merging：{FINAL_OUTPUT}")

# ========== 主函数 ==========
def main(args):
    if not args.merge_only:
        gz_files = [
            os.path.join(root, fname)[len(INPUT_FOLDER)+1:]
            for root, _, files in os.walk(INPUT_FOLDER)
            for fname in files if fname.endswith(".gz")
        ]
        print(f"Found {len(gz_files)}  .gz files，start extracting referenced_works...")

        with Pool(processes=max(cpu_count() // 2, 1)) as pool:
            list(tqdm(pool.imap_unordered(extract_references_streaming, gz_files), total=len(gz_files)))

    if not args.extract_only:
        merge_parquet_chunks()

# ========== CLI ==========
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract and merge OpenAlex references")
    parser.add_argument('--extract-only', action='store_true', help="Only extracting")
    parser.add_argument('--merge-only', action='store_true', help="Only merging")
    args = parser.parse_args()
    main(args)
