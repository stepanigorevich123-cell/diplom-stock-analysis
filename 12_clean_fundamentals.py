import pandas as pd
import numpy as np

INPUT_FILE  = r"D:\diplom\data\cbonds_msfo.csv"
OUTPUT_FILE = r"D:\diplom\data\cbonds_msfo.csv"

df = pd.read_csv(INPUT_FILE)
print(f"До: {len(df)} строк, {df['ticker'].nunique()} компаний")

# ── 1. Убираем RGSS ───────────────────────────────────────────────────────
df = df[df['ticker'] != 'RGSS'].reset_index(drop=True)
print(f"После удаления RGSS: {df['ticker'].nunique()} компаний")

# ── 2. Заполняем debt_total = debt_short + debt_long где пусто ────────────
mask = df['debt_total'].isna() & df['debt_short'].notna() & df['debt_long'].notna()
df.loc[mask, 'debt_total'] = df.loc[mask, 'debt_short'] + df.loc[mask, 'debt_long']
print(f"Заполнено debt_total из суммы краткосрочного и долгосрочного: {mask.sum()} строк")

# Где только одна из двух компонент есть — берём её
mask_short = df['debt_total'].isna() & df['debt_short'].notna() & df['debt_long'].isna()
mask_long  = df['debt_total'].isna() & df['debt_short'].isna()  & df['debt_long'].notna()
df.loc[mask_short, 'debt_total'] = df.loc[mask_short, 'debt_short']
df.loc[mask_long,  'debt_total'] = df.loc[mask_long,  'debt_long']
print(f"Заполнено debt_total только из краткосрочного: {mask_short.sum()} строк")
print(f"Заполнено debt_total только из долгосрочного:  {mask_long.sum()} строк")

# ── 3. Проверка что осталось пустым ──────────────────────────────────────
print("\nОставшиеся пропуски в debt_total:")
still_missing = df[df['debt_total'].isna()][['ticker','year']].groupby('ticker')['year'].apply(list)
if still_missing.empty:
    print("  Нет пропусков ✅")
else:
    for ticker, years in still_missing.items():
        print(f"  {ticker}: {years}")

# ── 4. Сохраняем ──────────────────────────────────────────────────────────
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nСохранено: {OUTPUT_FILE}")
print(f"Итого: {len(df)} строк, {df['ticker'].nunique()} компаний")