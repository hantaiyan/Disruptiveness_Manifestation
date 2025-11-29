# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

# ========= 配置路径 ==========
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 输入输出目录
BASE_MAPPING_DIR = BASE_DIR / "Disruptiveness-novelty" / "results"
BASE_OUT = BASE_DIR / "Disruptiveness-novelty" / "results" / "top5"
BASE_OUT.mkdir(parents=True, exist_ok=True)

# ========= 映射关系 ==========
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

# ========= 通用处理函数 ==========
def process_top5(orig_path, research_path):
    # 1. 加载数据
    df_all = pd.read_csv(orig_path)

    # 2. 提取 DI_yX 列（只要 y3-y15）
    di_cols = [
        col for col in df_all.columns
        if col.startswith("DI_y") and not col.endswith("_top5") and int(col.split("_")[1][1:]) >= 3
    ]

    # 3. 计算 Top5% 阈值
    thresholds = {col: df_all[col].quantile(0.95) for col in di_cols}
    print("阈值：", thresholds)

    # 4. 标记 top5
    for col in di_cols:
        df_all[col + "_top5"] = df_all[col] >= thresholds[col]

    # 5. 统计指标
    top5_flags = df_all[[col + "_top5" for col in di_cols]]
    df_all["years_in_top5"] = top5_flags.sum(axis=1)
    df_all["first_year_top5"] = top5_flags.apply(lambda row: row.idxmax() if row.any() else None, axis=1)
    df_all["last_year_top5"] = top5_flags.apply(lambda row: row[::-1].idxmax() if row.any() else None, axis=1)

    # 6. 筛选研究样本
    research_data = df_all[df_all["years_in_top5"] > 0].copy()

    # 7. 保存
    research_data.to_csv(research_path, index=False)
    print(f"已保存：{research_path} （{research_data.shape[0]} 条）\n")


# ========= 主循环 ==========
for year in years:
    for field in fields:
        print(f"\n处理 {year}-{field} ...")

        orig_path = BASE_MAPPING_DIR / f"{year}{field}_focal_DI_y1_to_y15.csv"

        if not orig_path.exists():
            print(f"跳过：未找到原始文件 {orig_path}")
            continue

        # 输出文件路径
        research_path = BASE_OUT / f"{year}{field}_focal_DI_top5_research_sample.csv"

        # 运行处理
        try:
            process_top5(orig_path, research_path)
        except Exception as e:
            print(f"出错：{year}-{field} {e}")
