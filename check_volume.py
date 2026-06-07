import pandas as pd
import glob
import os

DATA_DIR = r"D:\DATADIPLOM\companiesdata"

no_volume = []
for filepath in sorted(glob.glob(os.path.join(DATA_DIR, "*.xlsx"))):
    ticker = os.path.basename(filepath).replace('.xlsx', '')
    try:
        df = pd.read_excel(filepath, header=0, index_col=0)
        idx = [str(x).strip() for x in df.index.tolist()]
        if 'Объем' not in idx:
            no_volume.append(ticker)
    except:
        pass

if no_volume:
    print(f"Нет строки 'Объем' ({len(no_volume)}): {no_volume}")
else:
    print("У всех компаний есть строка 'Объем' ✅")