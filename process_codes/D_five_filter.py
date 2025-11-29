import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm

tqdm.pandas()

# ========= 配置路径 =========
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 输入输出子目录
BASE_MAPPING_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")
BASE_EDGES_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")
BASE_FILTERED_DIR = os.path.join(BASE_DIR, "Disruptiveness-novelty/results")

for d in [BASE_MAPPING_DIR, BASE_EDGES_DIR, BASE_FILTERED_DIR]:
    os.makedirs(d, exist_ok=True)

# ========= 配置领域和年份 =========
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

# ========= 主循环 =========
for field in fields:
    for year in years:
        print(f"正在处理 {year}-{field} extra focal filtering ...")

        # 输入映射表 & edges
        mapping_path = f"{BASE_MAPPING_DIR}/{year}{field}_focal_reference_mapping.csv"
        edges_path = f"{BASE_EDGES_DIR}/{year}{field}_citing_edges.csv"

        if not os.path.exists(mapping_path) or not os.path.exists(edges_path):
            print(f"跳过：未找到 {mapping_path} 或 {edges_path}")
            continue

        # 输出文件（筛选后映射）
        output_path = f"{BASE_FILTERED_DIR}/{year}{field}_focal_reference_mapping_filtered.csv"

        # ========= Step 1: 加载映射表 =========
        print("加载映射表...")
        df_map = pd.read_csv(mapping_path)

        # 标准化 reference_id
        df_map['reference_id'] = df_map['reference_id'].apply(
            lambda rid: rid if str(rid).startswith("https://openalex.org/") else "https://openalex.org/" + str(rid)
        )

        # ========= Step 2: 引用数量 ≥ 5 =========
        focal_ref_counts = df_map['focal_id'].value_counts()
        valid_focals_by_ref = set(focal_ref_counts[focal_ref_counts >= 5].index)

        # ========= Step 3: 被引用 ≥ 5 =========
        print("加载引用边表...")
        df_edges = pd.read_csv(edges_path)
        focal_cited_counts = df_edges['cited_id'].value_counts()
        valid_focals_by_cited = set(focal_cited_counts[focal_cited_counts >= 5].index)

        # ========= Step 4: 求交集 =========
        valid_focals_final = valid_focals_by_ref & valid_focals_by_cited
        print(f"{year}-{field}: 满足所有条件的 focal 数量：{len(valid_focals_final):,}")

        # ========= Step 5: 筛选 =========
        df_map_filtered = df_map[df_map['focal_id'].progress_apply(lambda x: x in valid_focals_final)]

        # 保存
        df_map_filtered.to_csv(output_path, index=False)
        print(f"筛选后映射表保存至：{output_path}，共 {len(df_map_filtered):,} 条")
