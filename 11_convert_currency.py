import pandas as pd
import numpy as np
import glob
import os

INPUT_FILE  = r"D:\diplom\data\cbonds_msfo.csv"
OUTPUT_FILE = r"D:\diplom\data\cbonds_msfo.csv"  # перезаписываем тот же файл
DATA_DIR    = r"D:\DATADIPLOM\companiesdata"

# Среднегодовые курсы ЦБ РФ
FX_USD = {2018: 62.9264, 2019: 64.6184, 2020: 72.3230, 2021: 73.6685,
          2022: 68.3522, 2023: 85.8116, 2024: 92.6567}
FX_EUR = {2018: 74.1330, 2019: 72.3187, 2020: 82.8358, 2021: 87.0861,
          2022: 72.1509, 2023: 92.8741, 2024: 100.2801}

NUMERIC_COLS = ['assets', 'debt_short', 'debt_long', 'equity', 'revenue', 'debt_total', 'ebitda']

# ── Шаг 1: определяем валюту каждой компании из Excel-файлов ──────────────
print("Читаю валюты из Excel файлов...")
ticker_currency = {}

for filepath in sorted(glob.glob(os.path.join(DATA_DIR, "*.xlsx"))):
    ticker = os.path.basename(filepath).replace('.xlsx', '')
    try:
        df = pd.read_excel(filepath, header=0, index_col=0)
        idx = [str(x).strip() for x in df.index.tolist()]
        if 'Валюта' in idx:
            row = df.iloc[idx.index('Валюта')].dropna()
            currency = str(row.values[0]).strip() if not row.empty else 'RUB'
        else:
            currency = 'RUB'
        ticker_currency[ticker] = currency
    except:
        ticker_currency[ticker] = 'RUB'

# Показываем не-рублёвые компании
non_rub = {t: c for t, c in ticker_currency.items() if c != 'RUB'}
print(f"\nНе-рублёвые компании ({len(non_rub)}):")
for t, c in non_rub.items():
    print(f"  {t}: {c}")

# ── Шаг 2: загружаем CSV и конвертируем ───────────────────────────────────
print(f"\nЧитаю {INPUT_FILE}...")
df = pd.read_csv(INPUT_FILE)
print(f"Строк до: {len(df)}, компаний: {df['ticker'].nunique()}")

converted = 0
for idx, row in df.iterrows():
    ticker = row['ticker']
    year   = int(row['year'])
    currency = ticker_currency.get(ticker, 'RUB')

    if currency == 'USD':
        fx = FX_USD.get(year, np.nan)
    elif currency == 'EUR':
        fx = FX_EUR.get(year, np.nan)
    else:
        continue  # RUB — ничего не делаем

    if np.isnan(fx):
        continue

    for col in NUMERIC_COLS:
        if col in df.columns and pd.notna(df.at[idx, col]):
            df.at[idx, col] = df.at[idx, col] * fx

    converted += 1

print(f"\nКонвертировано строк: {converted}")

# ── Шаг 3: сохраняем ──────────────────────────────────────────────────────
df.to_csv(OUTPUT_FILE, index=False)
print(f"Сохранено: {OUTPUT_FILE}")

# ── Шаг 4: проверка ───────────────────────────────────────────────────────
print("\nПроверка конвертированных компаний (2024):")
df24 = df[df['year'] == 2024]
for ticker in non_rub:
    row = df24[df24['ticker'] == ticker]
    if not row.empty:
        rev = row['revenue'].values[0]
        assets = row['assets'].values[0]
        ccy = non_rub[ticker]
        print(f"  {ticker} ({ccy}): выручка = {rev:,.1f} млн руб, активы = {assets:,.1f} млн руб")