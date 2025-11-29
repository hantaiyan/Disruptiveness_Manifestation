import pyarrow.dataset as ds
import pandas as pd
import csv
import numpy as np
from tqdm import tqdm
from pathlib import Path

# ========== 基础路径配置 ==========
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "Disruptiveness-novelty"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# 输入 Parquet（引用关系）
REFERENCES_PARQUET = BASE_DIR / "datasets" / "openalex-references.parquet"

# focal CSV 输入目录
BASE_FOCAL_DIR = BASE_DIR / "results"

# 映射关系输出目录
BASE_OUTPUT_DIR = BASE_DIR / "results"
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== 配置领域和年份 ==========
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]
years = [1999, 2004, 2009]

# ========== 加载 Dataset ==========
dataset = ds.dataset(REFERENCES_PARQUET, format="parquet")
scanner = dataset.scanner(columns=['id', 'referenced_works'])

# ========== 主循环 ==========
for field in fields:
    for year in years:
        print(f"\n正在处理 {year}-{field} focal references ...")

        # focal CSV 输入路径
        focal_csv_path = BASE_FOCAL_DIR / f"{year}{field}_ids_from_primary.csv"
        if not focal_csv_path.exists():
            print(f"跳过：未找到 {focal_csv_path}")
            continue

        # 输出路径
        output_txt_path = BASE_OUTPUT_DIR / f"{year}{field}_focal+reference_ids.txt"
        output_mapping_csv = BASE_OUTPUT_DIR / f"{year}{field}_focal_reference_mapping.csv"

        # 加载 focal paper IDs
        focal_ids = pd.read_csv(focal_csv_path)['id'].astype(str).tolist()
        focal_ids_set = set(focal_ids)
        print(f"加载 focal_id 数量：{len(focal_ids_set)}")

        # 初始化输出
        with open(output_mapping_csv, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['focal_id', 'reference_id'])

            all_ids_set = set()
            match_count = 0
            ref_written_count = 0
            ref_empty_count = 0

            # 遍历 Parquet 批次
            print("开始扫描 parquet 数据...")
            with tqdm(total=100000, desc=f"{year}-{field}", unit="条") as pbar:
                for batch in scanner.to_batches():
                    df = batch.to_pandas()
                    for _, row in df.iterrows():
                        pbar.update(1)

                        focal_id = row['id']
                        if focal_id not in focal_ids_set:
                            continue

                        references = row['referenced_works']

                        if not isinstance(references, (list, np.ndarray)) or len(references) == 0:
                            ref_empty_count += 1
                            continue

                        match_count += 1
                        for ref_id in references:
                            if ref_id:
                                csv_writer.writerow([focal_id, ref_id])
                                all_ids_set.add(focal_id)
                                all_ids_set.add(ref_id)
                                ref_written_count += 1

        # 写唯一 ID
        with open(output_txt_path, 'w') as f_txt:
            for _id in sorted(all_ids_set):
                f_txt.write(_id + '\n')

        # 打印统计
        print("处理完成。")
        print(f"匹配 focal_id 数量：{match_count}")
        print(f"映射写入条数：{ref_written_count}")
        print(f"空 reference focal_id 数量：{ref_empty_count}")
        print(f"唯一 ID 文件：{output_txt_path}")
        print(f"映射关系文件：{output_mapping_csv}")
