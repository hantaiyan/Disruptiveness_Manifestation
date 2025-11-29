import pyarrow.dataset as ds
import sqlite3
from tqdm import tqdm

# ========== 配置路径 ==========
# parquet_path = "/Users/zhaoxinhang/openalex-primary.parquet"
# sqlite_path = "/Users/zhaoxinhang/openalex-primary.sqlite"

parquet_path = "/Users/zhaoxinhang/N/openalex-primary.parquet"
sqlite_path = "/Users/zhaoxinhang/N/openalex-primary.sqlite"

# ========== 初始化 SQLite ==========
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

# ========== 使用 scanner 分批读取 ==========
dataset = ds.dataset(parquet_path, format="parquet")
scanner = dataset.scanner(columns=["id", "publication_date", "source_id", "source_type", "source_name", "issn_l"])

print("🚀 开始分批写入 SQLite...")
for batch in tqdm(scanner.to_batches(), desc="📦 插入中"):
    df = batch.to_pandas()
    values = df.values.tolist()

    cursor.executemany("""
        INSERT OR IGNORE INTO primary_source 
        (id, publication_date, source_id, source_type, source_name, issn_l) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, values)
    conn.commit()

conn.close()
print("✅ 所有数据已成功写入 SQLite！")
