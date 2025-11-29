# -*- coding: utf-8 -*-
import pandas as pd
import os
from pathlib import Path

# ========= 基础路径 ==========
BASE = Path(__file__).resolve().parent.parent.parent
BASE_DIR = BASE / "Disruptiveness-novelty"


BASE_DELAY = BASE_DIR / "results" / "top5"   # 包含 *_focal_top5_delay_years.csv
TEXTUAL_FILE = BASE_DIR / "datasets" / "papers_textual_metrics.csv"
BASE_OUT = BASE_DIR / "results" / "top5"
BASE_OUT.mkdir(parents=True, exist_ok=True)

# ========= 年份 & 领域 ==========
years = [1999, 2004, 2009]
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]

# ========= 读取文本指标 ==========
textual_df = pd.read_csv(TEXTUAL_FILE)
textual_df["PaperID"] = textual_df["PaperID"].astype(str)

# ========= 主循环 ==========
for year in years:
    for field in fields:
        in_path = BASE_DELAY / f"{year}{field}_focal_top5_delay_years.csv"
        out_path = BASE_OUT / f"{year}{field}_focal_paper_textual_metrics_with_focalid.csv"

        if not in_path.exists():
            print(f"跳过：未找到 {in_path}")
            continue

        print(f"\n正在处理: {in_path}")
        focal_df = pd.read_csv(in_path)

        # 提取纯 ID（W 开头）
        focal_df["pure_id"] = focal_df["focal_id"].astype(str).str.extract(r"(W\d+)$")
        focal_ids = set(focal_df["pure_id"].dropna())

        # 1) 只取这些论文的文本指标
        focal_textual_df = textual_df[textual_df["PaperID"].isin(focal_ids)].copy()

        # 2) 合并回 URL 版 focal_id（来自右表 focal_df）
        focal_textual_df = focal_textual_df.merge(
            focal_df[["focal_id", "pure_id"]],
            left_on="PaperID", right_on="pure_id",
            how="left"
        )

        # 2.5) 兜底：如果有些没拼上 URL，就用 PaperID 拼上前缀补齐
        mask_na = focal_textual_df["focal_id"].isna()
        if mask_na.any():
            focal_textual_df.loc[mask_na, "focal_id"] = (
                "https://openalex.org/" + focal_textual_df.loc[mask_na, "PaperID"].astype(str)
            )

        # 3) 只保留一个 focal_id（带前缀的），删除 PaperID / pure_id
        focal_textual_df = focal_textual_df.drop(columns=["PaperID", "pure_id"])

        # 4) 保存
        focal_textual_df.to_csv(out_path, index=False)
        print(f"✅ 已保存：{out_path}，共 {len(focal_textual_df)} 行（仅保留带前缀的 focal_id）")
