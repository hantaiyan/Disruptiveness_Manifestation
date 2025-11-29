# -*- coding: utf-8 -*-
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.compute as pc
import pyarrow as pa
from pathlib import Path
import re

# ========= ISSN 归一化函数 =========
def normalize_issn(raw):
    if not raw or not isinstance(raw, str):
        return None
    i = raw.strip().upper()
    i = i.replace(" ", "").replace("-", "").replace(";", ",").replace("/", ",").replace(".", "")
    if not all(c.isdigit() or c == "X" for c in i):
        return None
    if len(i) < 8:
        i = i.zfill(8)
    if len(i) == 8 and "-" not in i:
        i = i[:4] + "-" + i[4:]
    return i

# ========= 基础路径 ==========
BASE = Path(__file__).resolve().parent.parent.parent
BASE_DIR = BASE / "Disruptiveness-novelty"
TOP5_DIR = BASE_DIR / "results" / "top5"
PRIMARY_PARQUET = BASE_DIR / "datasets" / "openalex-primary.parquet"
SCIMAGO_DIR = BASE_DIR / "journalranks"

# ========= 加载 primary dataset ==========
dataset = ds.dataset(PRIMARY_PARQUET, format="parquet")

# ========= 遍历 delay_years 文件 ==========
for focal_file in TOP5_DIR.glob("*_focal_top5_delay_years.csv"):
    fname = focal_file.stem
    print(f"\n处理 {fname} ...")

    # 提取年份和领域
    m = re.match(r"(\d{4})([A-Za-z]+)_focal_top5_delay_years", fname)
    if not m:
        print(f"文件名无法解析: {fname}")
        continue
    year, field = m.groups()

    # Step 1. 读取 focal 文件
    id_df = pd.read_csv(focal_file)
    id_df["focal_id"] = id_df["focal_id"].astype(str)

    if not id_df["focal_id"].iloc[0].startswith("https://"):
        print("有缺少前缀的 id 数据")

    # Step 2. 从 primary 中提取 issn_l
    focal_ids = pa.array(id_df["focal_id"].tolist())
    filtered_table = dataset.to_table(
        filter=pc.is_in(pc.field("id"), value_set=focal_ids),
        columns=["id", "issn_l"]
    )
    filtered_df = filtered_table.to_pandas()
    merged = id_df.merge(filtered_df, left_on="focal_id", right_on="id", how="left")

    # Step 3. 清洗 issn
    merged["issn_clean"] = merged["issn_l"].astype(str).map(normalize_issn)

    # Step 4. 加载 SCImago 数据（改为固定目录）
    scimago_path = SCIMAGO_DIR / f"scimago-{year}-{field}.xlsx"
    if not scimago_path.exists():
        print(f"跳过：未找到 {scimago_path}")
        continue

    scimago_raw = pd.read_excel(scimago_path)

    # 拆分 & 清洗 ISSN
    scimago_rows = []
    for _, row in scimago_raw.iterrows():
        if pd.isna(row.get("Issn")):
            continue
        for raw_issn in str(row["Issn"]).split(","):
            issn_clean = normalize_issn(raw_issn)
            if issn_clean:
                scimago_rows.append({
                    "Title": row["Title"],
                    "SJR Best Quartile": row["SJR Best Quartile"],
                    "Issn_clean": issn_clean
                })
    scimago = pd.DataFrame(scimago_rows)

    # Step 5. 合并匹配
    final = merged.merge(scimago, left_on="issn_clean", right_on="Issn_clean", how="left")

    # Step 6. 输出
    output_path = TOP5_DIR / f"{year}{field}_top5_sjr.csv"
    final = final[["focal_id", "issn_clean", "SJR Best Quartile"]]
    final.to_csv(output_path, index=False)

    # Step 7. 日志
    match_count = final["SJR Best Quartile"].notna().sum()
    print(f"输出路径：{output_path}")
