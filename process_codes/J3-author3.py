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

# ========= 年份和领域 ==========
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

# ========= 主循环 ==========
for year in years:
    for field in fields:
        print(f"处理 {year}-{field} ...")

        in_path = f"{BASE}/{year}{field}_top5_focal_authors_with_prior_counts.csv"
        out_path = f"{BASE}/{year}{field}_top5_full_prior_stats.csv"

        if not os.path.exists(in_path):
            print(f"跳过：未找到 {in_path}")
            continue

        # Step 0: 读取并预处理
        df = pd.read_csv(in_path)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"work_id": "focal_id"})  # 兼容部分文件

        # 确认 prior 列名
        prior_col = [c for c in df.columns if c.startswith("prior_pubs_before_")]
        if len(prior_col) != 1:
            print(f"{in_path} 没有唯一的 prior 列，跳过")
            continue
        prior_col = prior_col[0]

        # Step 1: 第一作者
        first_authors = df[df['author_position'] == 'first'][['focal_id', prior_col]]
        first_authors_agg = first_authors.groupby('focal_id')[prior_col].mean().reset_index()
        first_authors_agg.rename(columns={prior_col: 'first_author_prior'}, inplace=True)

        # Step 2: 所有作者平均
        df_unique = df.drop_duplicates(subset=["focal_id", "author_id"])
        author_avg = df_unique.groupby('focal_id')[prior_col].mean().reset_index()
        author_avg.rename(columns={prior_col: 'avg_all_authors_prior'}, inplace=True)

        # Step 3: 作者数量
        author_count = df_unique.groupby('focal_id')['author_id'].count().reset_index()
        author_count.rename(columns={'author_id': 'author_count'}, inplace=True)

        # Step 4: 合并
        all_ids = df[['focal_id']].drop_duplicates()
        merged = (all_ids
                  .merge(first_authors_agg, on='focal_id', how='left')
                  .merge(author_avg, on='focal_id', how='left')
                  .merge(author_count, on='focal_id', how='left'))

        # Step 5: 保存
        merged.to_csv(out_path, index=False)
        print(f"已保存：{out_path}，共 {merged.shape[0]} 条记录，新增 author_count 指标")
