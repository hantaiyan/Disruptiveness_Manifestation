# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

# ========= 路径与参数 =========
BASE_DIR = Path("/Users/zhaoxinhang/Disruptiveness-novelty")
RESULTS_DIR = BASE_DIR / "results" / "top5"

years  = [1999, 2004, 2009]
fields = ["Chemistry", "Pharmacology", "Physics", "BMA"]

# 注意：改为 institution_country
REQUIRED_COLS = {"work_id", "author_id", "institution_country"}

def clean_country(c):
    """标准化国家码：去空格、转大写，把缺失同化为空字符串。"""
    if pd.isna(c):
        return ""
    c = str(c).strip().upper()
    return "" if c in {"", "NAN", "NA", "NONE", "NULL"} else c

def compute_international_by_paper(df: pd.DataFrame) -> pd.DataFrame:
    """
    依据你的规则计算每篇 paper 的国际合著指标。
    规则：
      - 若作者数 < 2 ⇒ international = 0
      - 否则，若全体作者的全部隶属国家（去重后）数 ≥ 2 ⇒ international = 1，否则 0
    输出列：
      work_id, n_authors, n_affiliations, n_countries, countries, is_international
    """
    # 必要列检查
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"缺少必要列: {missing}")

    # 标准化国家字段
    df = df.copy()
    df["institution_country"] = df["institution_country"].map(clean_country)

    def agg_one(sub: pd.DataFrame) -> pd.Series:
        n_authors = sub["author_id"].nunique()
        if n_authors >= 2:
            countries = sorted({c for c in sub["institution_country"].tolist() if c})
            n_countries = len(countries)
            is_international = 1 if n_countries >= 2 else 0
        else:
            countries = []
            n_countries = 0
            is_international = 0

        return pd.Series({
            "n_authors": n_authors,
            "n_affiliations": len(sub),
            "n_countries": n_countries,
            "countries": ",".join(countries),
            "is_international": is_international
        })

    out = (
        df.groupby("work_id", as_index=False)
          .apply(agg_one)
          .reset_index(drop=True)
    )
    return out

def run_one(year: int, field: str):
    in_file  = RESULTS_DIR / f"{year}{field}_top5_focal_authors_with_prior_counts.csv"
    out_file = RESULTS_DIR / f"{year}{field}_top5_focal_international.csv"
    if not in_file.exists():
        print(f"⚠️ 文件不存在，跳过：{in_file.name}")
        return
    print(f"Processing: {in_file.name}")

    # ===== 统一列名格式 =====
    df = pd.read_csv(in_file)
    df.columns = [c.strip() for c in df.columns]  # 去掉空格

    if "institution_country" not in df.columns:
        print(f"⚠️ {in_file.name} 缺少 institution_country 列，跳过。")
        return

    res = compute_international_by_paper(df)
    res.to_csv(out_file, index=False)
    print(f"→ Saved: {out_file.name} (rows={len(res)})")

if __name__ == "__main__":
    for y in years:
        for f in fields:
            try:
                run_one(y, f)
            except Exception as e:
                print(f"❌ 处理 {y}{f} 出错：{e}")
