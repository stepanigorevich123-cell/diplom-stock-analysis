import pandas as pd
import numpy as np
import glob
import os

DATA_DIR = r"D:\DATADIPLOM\companiesdata"

results = []

for filepath in sorted(glob.glob(os.path.join(DATA_DIR, "*.xlsx"))):
    ticker = os.path.basename(filepath).replace('.xlsx', '')
    if ticker.startswith('~$'):
        continue

    try:
        df = pd.read_excel(filepath, header=0, index_col=0)
    except Exception as e:
        results.append({'ticker': ticker, 'issue': f'ОШИБКА ЧТЕНИЯ: {e}'})
        continue

    idx = [str(x).strip() for x in df.index.tolist()]
    cols = df.columns.tolist()

    issues = []

    # 1. Валюта
    currency = 'RUB'
    if 'Валюта' in idx:
        row = df.iloc[idx.index('Валюта')].dropna()
        currency = str(row.values[0]).strip() if not row.empty else '???'
    else:
        issues.append('нет строки Валюта')

    # 2. Объем
    volume = None
    if 'Объем' in idx:
        row = df.iloc[idx.index('Объем')].dropna()
        try:
            volume = float(row.values[0])
        except:
            issues.append('Объем не число')
    else:
        issues.append('нет строки Объем')

    # 3. Какой квартал годовой
    has_q4 = any('IV кв.' in str(c) for c in cols)
    target_q = 'IV кв.' if has_q4 else 'I кв.'
    annual_cols = [c for c in cols if target_q in str(c)]

    # 4. Годы
    years = []
    for c in annual_cols:
        try:
            y = int(str(c).split('.')[-1].strip())
            if 2018 <= y <= 2024:
                years.append(y)
        except:
            pass

    # 5. Ключевые строки
    key_rows = {
        'Активы': 'assets',
        'Выручка': 'revenue',
        'Капитал': 'equity',
        'Краткосрочный долг': 'debt_short',
        'Долгосрочный долг': 'debt_long',
        'Общий долг': 'debt_total',
    }
    missing_rows = [name for name in key_rows if name not in idx]
    if missing_rows:
        issues.append(f'нет строк: {missing_rows}')

    # 6. Проверяем что активы и выручка не все NaN
    for row_name in ['Активы', 'Выручка']:
        if row_name not in idx:
            continue
        vals = []
        for c in annual_cols:
            try:
                v = df.iloc[idx.index(row_name)][c]
                if pd.notna(v) and str(v).strip() not in ('', '-'):
                    vals.append(float(v))
            except:
                pass
        if not vals:
            issues.append(f'{row_name}: все NaN')

    results.append({
        'ticker': ticker,
        'currency': currency,
        'volume': volume,
        'target_q': target_q,
        'years': sorted(years),
        'n_years': len(years),
        'issues': '; '.join(issues) if issues else '✅ OK',
    })

# ── Вывод ──────────────────────────────────────────────────────────────────
df_res = pd.DataFrame(results)

print("=" * 70)
print("ПРОБЛЕМНЫЕ КОМПАНИИ:")
print("=" * 70)
problems = df_res[df_res['issues'] != '✅ OK']
if problems.empty:
    print("Нет проблем!")
else:
    for _, row in problems.iterrows():
        print(f"{row['ticker']:8s} | {row['currency']} | vol={row['volume']} | {row['issues']}")

print()
print("=" * 70)
print("ВАЛЮТЫ:")
print("=" * 70)
for ccy, grp in df_res.groupby('currency'):
    print(f"  {ccy}: {sorted(grp['ticker'].tolist())}")

print()
print("=" * 70)
print("ЕДИНИЦЫ (Объем):")
print("=" * 70)
for vol, grp in df_res.groupby('volume'):
    print(f"  {int(vol):>10,}: {sorted(grp['ticker'].tolist())}")

print()
print("=" * 70)
print("КОЛИЧЕСТВО ЛЕТ ДАННЫХ:")
print("=" * 70)
for n, grp in df_res.groupby('n_years'):
    print(f"  {n} лет: {sorted(grp['ticker'].tolist())}")

print()
print(f"Всего файлов: {len(df_res)}")
print(f"С проблемами: {len(problems)}")
print(f"OK: {len(df_res) - len(problems)}")