# -*- coding: utf-8 -*-
import os
import glob
import pandas as pd
from pathlib import Path
from pathlib import Path

# ========= 基础路径 ==========
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ========= 基础路径 ==========
BASE = BASE_DIR / "Disruptiveness-novelty"
TOP5_DIR = BASE / "results" / "top5"

TARGET_COLS = ["SJR Best Quartile", "quartile_mode_15y", "quartile_avg_round_15y"]
UNRANKED_ALIASES = {"-", "UNRANKED", "NONE", ""}

def norm_quartile(val):
    """标准化为 Q1..Q4 或 Unranked"""
    if pd.isna(val):
        return "Unranked"
    s = str(val).strip().upper().replace(" ", "")
    if s in {"Q1","Q2","Q3","Q4"}: return s
    if s in UNRANKED_ALIASES: return "Unranked"
    # 数字兼容
    try:
        f = float(s)
        if f==1: return "Q1"
        if f==2: return "Q2"
        if f==3: return "Q3"
        if f==4: return "Q4"
        if f==5: return "Unranked"
    except: 
        pass
    return "Unranked"

MAPPINGS = {
    "bin_Q1":   {"Q1":1,"Q2":0,"Q3":0,"Q4":0,"Unranked":0},
    "ord_1to5":{"Q1":1,"Q2":2,"Q3":3,"Q4":4,"Unranked":5},
    "bin_Q12": {"Q1":1,"Q2":1,"Q3":0,"Q4":0,"Unranked":0},
    "bin_Q123":{"Q1":1,"Q2":1,"Q3":1,"Q4":0,"Unranked":0},
}

def process_file(path: Path):
    df = pd.read_csv(path)
    for col in TARGET_COLS:
        if col in df.columns:
            norm_col = f"{col}__norm"
            df[norm_col] = df[col].apply(norm_quartile)
            for k, mp in MAPPINGS.items():
                df[f"{col}_{k}"] = df[norm_col].map(mp)
    # 兼容旧的 quartile_numeric：基于 SJR Best Quartile 的 bin_Q1
    if "SJR Best Quartile__norm" in df.columns:
        df["quartile_numeric"] = df["SJR Best Quartile__norm"].map(MAPPINGS["bin_Q1"])

    out = path.with_name(path.name.replace("_with_15y_quartiles.csv","_focal_with_quartiledata.csv"))
    df.to_csv(out,index=False)
    print(f"完成：{out}")

def main():
    files = glob.glob(str(TOP5_DIR / "*_with_15y_quartiles.csv"))
    if not files:
        print("没找到任何 *_with_15y_quartiles.csv 文件")
    for f in files:
        process_file(Path(f))

if __name__=="__main__":
    main()
