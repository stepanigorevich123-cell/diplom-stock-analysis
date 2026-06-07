import pandas as pd
import numpy as np
import glob
import os

INPUT_FILE  = r"D:\diplom\data\cbonds_msfo.csv"
OUTPUT_FILE = r"D:\diplom\data\cbonds_msfo.csv"
DATA_DIR    = r"D:\DATADIPLOM\companiesdata"

# Среднегодовые курсы ЦБ РФ
FX_USD = {2018: 62.9264, 2019: 64.6184, 2020: 72.3230, 2021: 73.6685,
          2022: 68.3522, 2023: 85.8116, 2024: 92.6567}
FX_EUR = {2018: 74.1330, 2019: 72.3187, 2020: 82.8358, 2021: 87.0861,
          2022: 72.1509, 2023: 92.8741, 2024: 100.2801}

NUMERIC_COLS = ['assets', 'debt_short', 'debt_long', 'equity',
                'revenue', 'debt_total', 'ebitda']

# ── Шаг 0: читаем валюту и объем из Excel ─────────────────────────────────
print("Читаю метаданные из Excel файлов...")
ticker_meta = {}

for filepath in sorted(glob.glob(os.path.join(DATA_DIR, "*.xlsx"))):
    ticker = os.path.basename(filepath).replace('.xlsx', '')
    if ticker.startswith('~$'):
        continue
    try:
        df = pd.read_excel(filepath, header=0, index_col=0)
        idx = [str(x).strip() for x in df.index.tolist()]

        # Валюта
        currency = 'RUB'
        if 'Валюта' in idx:
            row = df.iloc[idx.index('Валюта')].dropna()
            if not row.empty:
                currency = str(row.values[0]).strip()

        # Объем (единицы)
        volume = 1_000_000
        if 'Объем' in idx:
            row = df.iloc[idx.index('Объем')].dropna()
            if not row.empty:
                volume = float(row.values[0])

        ticker_meta[ticker] = {'currency': currency, 'volume': volume}
    except:
        ticker_meta[ticker] = {'currency': 'RUB', 'volume': 1_000_000}

# ── Шаг 1: загружаем CSV ──────────────────────────────────────────────────
df = pd.read_csv(INPUT_FILE)
print(f"\nДо очистки: {len(df)} строк, {df['ticker'].nunique()} компаний")

# ── Шаг 2: удаляем ненужные компании ─────────────────────────────────────
exclude = ['ETLN', 'FIXR', 'RGSS', 'USBN']
df = df[~df['ticker'].isin(exclude)].reset_index(drop=True)
print(f"После удаления {exclude}: {df['ticker'].nunique()} компаний")

# ── Шаг 3: исправляем ROSN (данные в миллиардах → делим на 1000) ──────────
# Объем ROSN = 1,000,000,000 → данные в млрд → нам нужны млн → делим на 1000
rosn_mask = df['ticker'] == 'ROSN'
for col in NUMERIC_COLS:
    if col in df.columns:
        df.loc[rosn_mask, col] = df.loc[rosn_mask, col] / 1000
print(f"ROSN: данные пересчитаны из млрд в млн руб")
print(f"  Выручка ROSN 2024: {df.loc[rosn_mask & (df['year']==2024), 'revenue'].values[0]:,.1f} млн руб")

# ── Шаг 4: конвертация валют в рубли ─────────────────────────────────────
print("\nКонвертация валют...")
converted_rows = 0
for idx_row, row in df.iterrows():
    ticker = row['ticker']
    year = int(row['year'])
    meta = ticker_meta.get(ticker, {})
    currency = meta.get('currency', 'RUB')

    if currency == 'USD':
        fx = FX_USD.get(year, np.nan)
    elif currency == 'EUR':
        fx = FX_EUR.get(year, np.nan)
    else:
        continue

    if np.isnan(fx):
        continue

    for col in NUMERIC_COLS:
        if col in df.columns and pd.notna(df.at[idx_row, col]):
            df.at[idx_row, col] = df.at[idx_row, col] * fx

    converted_rows += 1

non_rub = {t: m['currency'] for t, m in ticker_meta.items() if m['currency'] != 'RUB'}
print(f"Конвертировано строк: {converted_rows}")
print(f"Компании не в рублях: {non_rub}")

# ── Шаг 5: заполняем debt_total = debt_short + debt_long где пусто ────────
print("\nЗаполнение debt_total...")
mask_both = df['debt_total'].isna() & df['debt_short'].notna() & df['debt_long'].notna()
df.loc[mask_both, 'debt_total'] = df.loc[mask_both, 'debt_short'] + df.loc[mask_both, 'debt_long']

mask_short = df['debt_total'].isna() & df['debt_short'].notna() & df['debt_long'].isna()
mask_long  = df['debt_total'].isna() & df['debt_short'].isna()  & df['debt_long'].notna()
df.loc[mask_short, 'debt_total'] = df.loc[mask_short, 'debt_short']
df.loc[mask_long,  'debt_total'] = df.loc[mask_long,  'debt_long']
print(f"Заполнено из суммы: {mask_both.sum()}, только short: {mask_short.sum()}, только long: {mask_long.sum()}")

# ── Шаг 6: сохраняем ──────────────────────────────────────────────────────
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nСохранено: {OUTPUT_FILE}")
print(f"Итого: {len(df)} строк, {df['ticker'].nunique()} компаний")

# ── Шаг 7: финальная проверка ─────────────────────────────────────────────
print("\n=== ФИНАЛЬНАЯ ПРОВЕРКА (выручка 2024, топ-10) ===")
df24 = df[df['year'] == 2024][['ticker','revenue','assets','equity']].copy()
df24 = df24.sort_values('revenue', ascending=False).head(10)
print(df24.to_string(index=False))

print("\n=== ПРОВЕРКА КОНВЕРТИРОВАННЫХ КОМПАНИЙ (2024) ===")
for ticker, ccy in non_rub.items():
    row = df[(df['ticker']==ticker) & (df['year']==2024)]
    if not row.empty:
        rev = row['revenue'].values[0]
        assets = row['assets'].values[0]
        print(f"  {ticker} ({ccy}→RUB): выручка={rev:>12,.1f} млн руб | активы={assets:>12,.1f} млн руб")

print("\n=== ПРОПУСКИ В КЛЮЧЕВЫХ ПОЛЯХ ===")
for col in ['assets', 'revenue', 'equity']:
    n_missing = df[df[col].isna()]['ticker'].nunique()
    print(f"  {col}: пропуски у {n_missing} компаний")