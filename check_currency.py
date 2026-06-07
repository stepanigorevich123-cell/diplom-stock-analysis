import pandas as pd
import glob
import os

DATA_DIR = r"D:\DATADIPLOM\companiesdata"

usd = []
rub = []
other = []

for filepath in sorted(glob.glob(os.path.join(DATA_DIR, "*.xlsx"))):
    ticker = os.path.basename(filepath).replace('.xlsx', '')
    try:
        df = pd.read_excel(filepath, header=0, index_col=0)
        idx = [str(x).strip() for x in df.index.tolist()]
        if 'Валюта' in idx:
            row = df.iloc[idx.index('Валюта')].dropna()
            currency = str(row.values[0]).strip() if not row.empty else 'N/A'
        else:
            currency = 'НЕТ СТРОКИ'

        if currency == 'USD':
            usd.append(ticker)
        elif currency == 'RUB':
            rub.append(ticker)
        else:
            other.append((ticker, currency))
    except Exception as e:
        other.append((ticker, f'ОШИБКА: {e}'))

print(f"=== USD ({len(usd)} компаний) ===")
print(', '.join(usd))

print(f"\n=== RUB ({len(rub)} компаний) ===")
print(', '.join(rub))

if other:
    print(f"\n=== ПРОЧЕЕ / ОШИБКИ ({len(other)}) ===")
    for t, c in other:
        print(f"  {t}: {c}")