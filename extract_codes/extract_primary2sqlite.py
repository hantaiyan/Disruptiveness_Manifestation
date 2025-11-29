import pyarrow.dataset as ds
import sqlite3
from tqdm import tqdm

# parquet_path = "/Users/zhaoxinhang/openalex-primary.parquet"
# sqlite_path = "/Users/zhaoxinhang/openalex-primary.sqlite"

parquet_path = "/Users/zhaoxinhang/N/openalex-primary.parquet"
sqlite_path = "/Users/zhaoxinhang/N/openalex-primary.sqlite"

conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS primary_source (
    id TEXT PRIMARY KEY,
    publication_date TEXT,
    source_id TEXT,
    source_type TEXT,
    source_name TEXT,
    issn_l TEXT
)
""")
conn.commit()

dataset = ds.dataset(parquet_path, format="parquet")
scanner = dataset.scanner(columns=["id", "publication_date", "source_id", "source_type", "source_name", "issn_l"])

for batch in tqdm(scanner.to_batches(), desc="insert"):
    df = batch.to_pandas()
    values = df.values.tolist()

    cursor.executemany("""
        INSERT OR IGNORE INTO primary_source 
        (id, publication_date, source_id, source_type, source_name, issn_l) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, values)
    conn.commit()

conn.close()
