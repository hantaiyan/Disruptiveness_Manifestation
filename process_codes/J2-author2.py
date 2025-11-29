# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
import pyarrow.dataset as ds
import os
from collections import defaultdict

# ========= 基础路径配置 ==========
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE = BASE_DIR / "Disruptiveness-novelty" / "results" / "top5"
BASE.mkdir(parents=True, exist_ok=True)

# ========= 数据路径 ==========
AUTHORS_PARQUET = BASE_DIR / "Disruptiveness-novelty/datasets/openalex-authors.parquet"
REFERENCES_PARQUET = BASE_DIR / "Disruptiveness-novelty/datasets/openalex-references.parquet"

# ========= 年份和领域 ==========
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

# ========= 打开 datasets ==========
authors_ds = ds.dataset(AUTHORS_PARQUET, format="parquet")
refs_ds = ds.dataset(REFERENCES_PARQUET, format="parquet")

# ========= 主循环 ==========
for year in years:
    for field in fields:
        print(f"处理 {year}-{field} ...")

        # 输入文件
        in_path = f"{BASE}/{year}{field}_top5_focal_authors.parquet"
        if not os.path.exists(in_path):
            print(f"跳过：未找到 {in_path}")
            continue

        # 输出文件
        out_path = f"{BASE}/{year}{field}_top5_focal_authors_with_prior_counts.csv"

        # ===== 步骤1：加载 focal 作者列表 =====
        focal_df = pd.read_parquet(in_path)
        if "author_id" not in focal_df.columns:
            print(f"{in_path} 缺少 author_id 列，跳过")
            continue

        focal_author_ids = focal_df["author_id"].dropna().unique().tolist()
        focal_author_set = set(focal_author_ids)

        if len(focal_author_set) == 0:
            print(f"{year}-{field} 没有作者，跳过")
            continue

        # ===== 步骤2：提取这些作者的历史 work_id =====
        author_to_works = defaultdict(set)
        for batch in authors_ds.to_batches(columns=["author_id", "work_id"]):
            df = batch.to_pandas()
            df = df[df["author_id"].isin(focal_author_set)]
            for _, row in df.iterrows():
                author_to_works[row["author_id"]].add(row["work_id"])

        # ===== 步骤3：从 primary 中提取对应 work 的年份 =====
        all_work_ids = set(w for works in author_to_works.values() for w in works)
        work_to_year = {}
        for batch in refs_ds.to_batches(columns=["id", "publication_date"]):
            df = batch.to_pandas()
            df = df[df["id"].isin(all_work_ids)]
            df["year"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.year
            for _, row in df.iterrows():
                work_to_year[row["id"]] = row["year"]

        # ===== 步骤4：统计每个作者在 focal 年份之前的发文数量 =====
        cutoff_year = year  # 统计截止点就是 focal 年份
        author_prior_counts = {
            author: sum(1 for wid in works if work_to_year.get(wid, 9999) < cutoff_year)
            for author, works in author_to_works.items()
        }

        # ===== 步骤5：合并并保存 =====
        focal_df[f"prior_pubs_before_{year}"] = focal_df["author_id"].map(author_prior_counts)
        focal_df.to_csv(out_path, index=False)
        print(f"保存成功：{out_path}，共 {focal_df.shape[0]} 行")
