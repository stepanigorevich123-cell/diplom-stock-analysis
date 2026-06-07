import pandas as pd
import numpy as np
import glob
import os

INPUT_FILE  = r"D:\diplom\data\cbonds_msfo.csv"
OUTPUT_FILE = r"D:\diplom\data\cbonds_msfo.csv"
DATA_DIR    = r"D:\DATADIPLOM\companiesdata"
FX_AVG_FILE = r"D:\diplom\data\fx_rates_avg.csv"
FX_EOY_FILE = r"D:\diplom\data\fx_rates_eoy.csv"

# Строки P&L — среднегодовой курс
PNL_COLS     = ['revenue', 'ebitda']
# Балансовые строки — курс на конец года
BALANCE_COLS = ['assets', 'debt_short', 'debt_long', 'equity', 'debt_total']

# ── Курсы валют ───────────────────────────────────────────────────────────
fx_avg = pd.read_csv(FX_AVG_FILE).set_index('year')
fx_eoy = pd.read_csv(FX_EOY_FILE).set_index('year')

def get_rate(df_fx, year, currency):
    try:
        return float(df_fx.loc[year, currency])
    except:
        return np.nan

# ── Метаданные из Excel (валюта каждой компании) ──────────────────────────
print("Читаю валюты из Excel файлов...")
ticker_currency = {}
for filepath in sorted(glob.glob(os.path.join(DATA_DIR, "*.xlsx"))):
    ticker = os.path.basename(filepath).replace('.xlsx', '')
    if ticker.startswith('~$'):
        continue
    try:
        df = pd.read_excel(filepath, header=0, index_col=0)
        idx = [str(x).strip() for x in df.index.tolist()]
        currency = 'RUB'
        if 'Валюта' in idx:
            row = df.iloc[idx.index('Валюта')].dropna()
            if not row.empty:
                currency = str(row.values[0]).strip()
        ticker_currency[ticker] = currency
    except:
        ticker_currency[ticker] = 'RUB'

non_rub = {t: c for t, c in ticker_currency.items() if c != 'RUB'}
print(f"Не-рублёвые компании: {non_rub}")

# ── Загружаем CSV ─────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_FILE)
print(f"\nДо: {len(df)} строк, {df['ticker'].nunique()} компаний")

# ── Удаляем ненужные компании ─────────────────────────────────────────────
exclude = ['ETLN', 'FIXR', 'RGSS', 'USBN']
df = df[~df['ticker'].isin(exclude)].reset_index(drop=True)
print(f"После удаления {exclude}: {df['ticker'].nunique()} компаний")

# ── Исправляем ROSN (данные в млрд → делим на 1000 → млн) ────────────────
rosn_mask = df['ticker'] == 'ROSN'
for col in PNL_COLS + BALANCE_COLS:
    if col in df.columns:
        df.loc[rosn_mask, col] = df.loc[rosn_mask, col] / 1000
rosn_rev = df.loc[rosn_mask & (df['year'] == 2024), 'revenue'].values
print(f"ROSN исправлен. Выручка 2024: {rosn_rev[0]:,.1f} млн руб" if len(rosn_rev) else "ROSN 2024 не найден")

# ── Конвертация валют ─────────────────────────────────────────────────────
print("\nКонвертация валют...")
converted = 0
for idx_row, row in df.iterrows():
    ticker = row['ticker']

    # NBIS → это Яндекс, тикер уже переименован в YDEX при парсинге
    currency = ticker_currency.get(ticker, 'RUB')
    if currency == 'RUB':
        continue

    year = int(row['year'])

    # P&L — среднегодовой курс
    fx_pnl = get_rate(fx_avg, year, currency)
    for col in PNL_COLS:
        if col in df.columns and pd.notna(df.at[idx_row, col]):
            df.at[idx_row, col] = df.at[idx_row, col] * fx_pnl

    # Баланс — курс на конец года
    fx_bal = get_rate(fx_eoy, year, currency)
    for col in BALANCE_COLS:
        if col in df.columns and pd.notna(df.at[idx_row, col]):
            df.at[idx_row, col] = df.at[idx_row, col] * fx_bal

    converted += 1

print(f"Конвертировано строк: {converted}")

# ── Заполняем debt_total = debt_short + debt_long где пусто ──────────────
print("\nЗаполнение debt_total...")
mask_both  = df['debt_total'].isna() & df['debt_short'].notna() & df['debt_long'].notna()
mask_short = df['debt_total'].isna() & df['debt_short'].notna() & df['debt_long'].isna()
mask_long  = df['debt_total'].isna() & df['debt_short'].isna()  & df['debt_long'].notna()
df.loc[mask_both,  'debt_total'] = df.loc[mask_both,  'debt_short'] + df.loc[mask_both, 'debt_long']
df.loc[mask_short, 'debt_total'] = df.loc[mask_short, 'debt_short']
df.loc[mask_long,  'debt_total'] = df.loc[mask_long,  'debt_long']
print(f"Заполнено: оба={mask_both.sum()}, только short={mask_short.sum()}, только long={mask_long.sum()}")

# ── Сохраняем ─────────────────────────────────────────────────────────────
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nСохранено: {OUTPUT_FILE}")
print(f"Итого: {len(df)} строк, {df['ticker'].nunique()} компаний")

# ── Проверка ──────────────────────────────────────────────────────────────
print("\n=== ПРОВЕРКА КОНВЕРТИРОВАННЫХ КОМПАНИЙ (2024) ===")
df24 = df[df['year'] == 2024]
for ticker, ccy in non_rub.items():
    row = df24[df24['ticker'] == ticker]
    if not row.empty:
        rev    = row['revenue'].values[0]
        assets = row['assets'].values[0]
        print(f"  {ticker:6s} ({ccy}→RUB): выручка={rev:>12,.1f} | активы={assets:>12,.1f}  млн руб")

print("\n=== ТОП-10 ПО ВЫРУЧКЕ 2024 ===")
top = df24[['ticker','revenue','assets']].sort_values('revenue', ascending=False).head(10)
print(top.to_string(index=False))