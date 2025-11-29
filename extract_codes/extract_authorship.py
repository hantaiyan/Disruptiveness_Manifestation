import os
import gzip
import json
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm
import glob

# ========== 路径配置 ==========
INPUT_FOLDER = "/Users/zhaoxinhang/openalex-snapshot/data/works"  
OUTPUT_FILE = "/Users/zhaoxinhang/datasets/openalex-authors.parquet"

# ========== Parquet schema ==========
schema = pa.schema([
    ("work_id", pa.string()),
    ("author_position", pa.string()),
    ("author_id", pa.string()),
    ("author_name", pa.string()),
    ("author_orcid", pa.string()),
    ("institution_id", pa.string()),
    ("institution_name", pa.string()),
    ("institution_country", pa.string()),
])

# ========== 扫描所有 .gz 文件 ==========
gz_files = sorted(glob.glob(os.path.join(INPUT_FOLDER, "**/*.gz"), recursive=True))
print(f"🔍 共发现 .gz 文件数：{len(gz_files)}")

# ========== 初始化写入器 ==========
writer = None
buffer = []
batch_size = 5000

# ========== 遍历文件并提取数据 ==========
for filepath in tqdm(gz_files):
    with gzip.open(filepath, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                work = json.loads(line)
                work_id = work.get("id")
                for auth in work.get("authorships", []):
                    author = auth.get("author", {})
                    institutions = auth.get("institutions", [])

                    if institutions:
                        for inst in institutions:
                            row = {
                                "work_id": work_id,
                                "author_position": auth.get("author_position"),
                                "author_id": author.get("id"),
                                "author_name": author.get("display_name"),
                                "author_orcid": author.get("orcid"),
                                "institution_id": inst.get("id"),
                                "institution_name": inst.get("display_name"),
                                "institution_country": inst.get("country_code"),
                            }
                            buffer.append(row)
                    else:
                        # 没有结构化机构信息的情况也要记录
                        raw_aff = auth.get("raw_affiliation_strings", [""])[0] if auth.get("raw_affiliation_strings") else ""
                        row = {
                            "work_id": work_id,
                            "author_position": auth.get("author_position"),
                            "author_id": author.get("id"),
                            "author_name": author.get("display_name"),
                            "author_orcid": author.get("orcid"),
                            "institution_id": None,
                            "institution_name": raw_aff,
                            "institution_country": None,
                        }
                        buffer.append(row)


                # 批量写入 parquet
                if len(buffer) >= batch_size:
                    table = pa.Table.from_pylist(buffer, schema=schema)
                    if writer is None:
                        writer = pq.ParquetWriter(OUTPUT_FILE, schema)
                    writer.write_table(table)
                    buffer.clear()

            except Exception:
                continue

# ========== 写入剩余数据 ==========
if buffer:
    table = pa.Table.from_pylist(buffer, schema=schema)
    if writer is None:
        writer = pq.ParquetWriter(OUTPUT_FILE, schema)
    writer.write_table(table)

if writer:
    writer.close()

print("✅ 提取完毕！文件保存为：", OUTPUT_FILE)
