import pandas as pd
import sqlite3
import os

# ========== Path ==========
ARTS_ID_FILE = '/Users/zhaoxinhang/datasets/papers_textual_metrics.csv'
INPUT_SQLITE = '/Users/zhaoxinhang/datasets/openalex-primary.sqlite'
OUTPUT_SQLITE = '/Users/zhaoxinhang/datasets/openalex-arts.sqlite'
TABLE_NAME = 'primary_source'  

# ========== 加载ARTs论文ID ==========
arts_df = pd.read_csv(ARTS_ID_FILE, usecols=['PaperID'])
arts_df['PaperID'] = 'https://openalex.org/' + arts_df['PaperID'].astype(str)
arts_ids = arts_df['PaperID'].dropna().unique().tolist()

# ========== 分批处理配置 ==========
batch_size = 10000
batches = [arts_ids[i:i+batch_size] for i in range(0, len(arts_ids), batch_size)]

# ========== 准备输出数据库 ==========
if os.path.exists(OUTPUT_SQLITE):
    os.remove(OUTPUT_SQLITE)  # 删除旧文件，避免表已存在问题
out_conn = sqlite3.connect(OUTPUT_SQLITE)

# ========== 连接原始数据库并执行查询 ==========
in_conn = sqlite3.connect(INPUT_SQLITE)
for idx, batch in enumerate(batches):
    placeholders = ','.join(['?'] * len(batch))
    query = f"SELECT * FROM [{TABLE_NAME}] WHERE id IN ({placeholders})"
    batch_df = pd.read_sql_query(query, in_conn, params=batch)
    
    # 分批写入输出数据库（第一次创建表，后续追加）
    batch_df.to_sql(TABLE_NAME, out_conn, index=False, if_exists='append')
    print(f"已处理第 {idx+1}/{len(batches)} 批，记录数：{len(batch_df)}")

# ========== 关闭连接 ==========
in_conn.close()
out_conn.close()

print(f"所有ARTs论文的 primary 子集已保存到：{OUTPUT_SQLITE}")
