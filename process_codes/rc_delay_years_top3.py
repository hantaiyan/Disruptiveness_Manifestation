import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BASE = BASE_DIR / "Disruptiveness-novelty" / "results" / "top3"

years = [1999, 2004, 2009]
fields = ["BMA", "Chemistry", "Pharmacology", "Physics"]

for year in years:
    for field in fields:
        in_path = BASE / f"{year}{field}_focal_DI_top3_research_sample.csv"
        out_path = BASE / f"{year}{field}_focal_top3_delay_years.csv"

        if not in_path.exists():
            print("pass")
            continue

        df = pd.read_csv(in_path)

        results = []
        for _, row in df.iterrows():
            focal_id = row["focal_id"]
            delay = None
            for y in range(3, 16):  # y3 ~ y15
                col = f"DI_y{y}_top3"
                val = str(row.get(col)).strip().upper()
                if val == "TRUE":
                    delay = y - 3
                    break
            results.append({"focal_id": focal_id, "delay_years_to_top3": delay})

        df_out = pd.DataFrame(results)
        df_out.to_csv(out_path, index=False)
