import pandas as pd
import pyarrow.dataset as ds
import pyarrow.compute as pc
import pyarrow as pa
import pyarrow.parquet as pq
import os
from pathlib import Path

# ========= 基础路径配置 ==========
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE = BASE_DIR / "Disruptiveness-novelty" / "results" / "top5"
BASE.mkdir(parents=True, exist_ok=True)

AUTHORS_PARQUET = BASE_DIR / "Disruptiveness-novelty/datasets/openalex-authors.parquet"
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]


# ========= 作者数据集 ==========
authors_ds = ds.dataset(AUTHORS_PARQUET, format="parquet")

# ========= 主循环 ==========
for year in years:
    for field in fields:
        print(f"处理 {year}-{field} ...")

        # 输入文件（Top5 样本）
        top5_path = f"{BASE}/{year}{field}_focal_DI_top5_research_sample.csv"
        if not os.path.exists(top5_path):
            print(f"跳过：未找到 {top5_path}")
            continue

        # 输出文件
        output_path = f"{BASE}/{year}{field}_top5_focal_authors.parquet"

        # 读取 focal paper IDs
        focal_df = pd.read_csv(top5_path)
        if "focal_id" not in focal_df.columns:
            print(f"{top5_path} 缺少 focal_id 列，跳过")
            continue
        focal_ids = focal_df["focal_id"].astype(str).unique().tolist()

        if len(focal_ids) == 0:
            print(f"{year}-{field} 没有 focal_id，跳过")
            continue

        # 构造筛选表达式
        focal_id_array = pa.array(focal_ids, type=pa.string())
        filter_expr = pc.is_in(ds.field("work_id"), value_set=focal_id_array)

        # 筛选
        filtered_table = authors_ds.to_table(filter=filter_expr)

        # 写 parquet
        pq.write_table(filtered_table, output_path)
        print(f"筛选完成，保存至: {output_path}，共 {filtered_table.num_rows:,} 行")
