import pandas as pd
import sqlite3
import os

ARTS_ID_FILE = '/Users/zhaoxinhang/datasets/papers_textual_metrics.csv'
INPUT_SQLITE = '/Users/zhaoxinhang/datasets/openalex-primary.sqlite'
OUTPUT_SQLITE = '/Users/zhaoxinhang/datasets/openalex-arts.sqlite'
TABLE_NAME = 'primary_source'  

arts_df = pd.read_csv(ARTS_ID_FILE, usecols=['PaperID'])
arts_df['PaperID'] = 'https://openalex.org/' + arts_df['PaperID'].astype(str)
arts_ids = arts_df['PaperID'].dropna().unique().tolist()

batch_size = 10000
batches = [arts_ids[i:i+batch_size] for i in range(0, len(arts_ids), batch_size)]

if os.path.exists(OUTPUT_SQLITE):
    os.remove(OUTPUT_SQLITE)  
out_conn = sqlite3.connect(OUTPUT_SQLITE)

in_conn = sqlite3.connect(INPUT_SQLITE)
for idx, batch in enumerate(batches):
    placeholders = ','.join(['?'] * len(batch))
    query = f"SELECT * FROM [{TABLE_NAME}] WHERE id IN ({placeholders})"
    batch_df = pd.read_sql_query(query, in_conn, params=batch)
    
    batch_df.to_sql(TABLE_NAME, out_conn, index=False, if_exists='append')

in_conn.close()
out_conn.close()
