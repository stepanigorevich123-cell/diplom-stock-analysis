import pandas as pd
import numpy as np
import os
import glob

DATA_DIR    = r"D:\DATADIPLOM\companiesdata"
OUTPUT_FILE = r"D:\diplom\data\cbonds_msfo.csv"
FX_AVG_FILE = r"D:\diplom\data\fx_rates_avg.csv"
FX_EOY_FILE = r"D:\diplom\data\fx_rates_eoy.csv"

# P&L — среднегодовой курс; Баланс — курс на конец года
PNL_COLS     = ['revenue', 'ebitda']
BALANCE_COLS = ['assets', 'debt_short', 'debt_long', 'equity', 'debt_total']

TARGET_ROWS = {
    'assets':     'Активы',
    'debt_short': 'Краткосрочный долг',
    'debt_long':  'Долгосрочный долг',
    'equity':     'Капитал',
    'revenue':    'Выручка',
    'debt_total': 'Общий долг',
    'ebitda':     'EBITDA',
}

# Специальные файлы: имя → тикер + какие годы брать
SPECIAL_FILES = {
    'NBIS':     {'ticker': 'YDEX', 'years': list(range(2018, 2024))},
    'HEAD_OLD': {'ticker': 'HEAD', 'years': list(range(2019, 2023))},
    'VKCO_OLD': {'ticker': 'VKCO', 'years': list(range(2018, 2022))},
}

# ROSN отчитывается в млрд руб (Объем=1_000_000_000)
# нам нужны млн руб → умножаем на 1000
SCALE_OVERRIDE = {
    'ROSN': 1000.0,
}

# ── Курсы валют ───────────────────────────────────────────────────────────
fx_avg = pd.read_csv(FX_AVG_FILE).set_index('year')
fx_eoy = pd.read_csv(FX_EOY_FILE).set_index('year')

def get_fx(year, currency, rate_type):
    df_fx = fx_avg if rate_type == 'avg' else fx_eoy
    try:
        return float(df_fx.loc[year, currency])
    except:
        return np.nan

# ── Вспомогательные функции ───────────────────────────────────────────────
def get_str(df, row_name):
    """Получить строковое значение из первой непустой ячейки строки."""
    idx = [str(x).strip() for x in df.index.tolist()]
    if row_name not in idx:
        return None
    row = df.iloc[idx.index(row_name)].dropna()
    if row.empty:
        return None
    return str(row.values[0]).strip()

def get_val(df, row_name, col):
    """Получить числовое значение из конкретной ячейки."""
    idx = [str(x).strip() for x in df.index.tolist()]
    if row_name not in idx:
        return np.nan
    try:
        val = df.iloc[idx.index(row_name)][col]
        if pd.notna(val) and str(val).strip() not in ('', '-'):
            return float(val)
    except:
        pass
    return np.nan

def get_column_scale(df, col, filename):
    """
    Получить масштаб (scale) для КОНКРЕТНОГО столбца.
    Читает значение строки 'Объем' в данном столбце.
    Если Объем не найден — по умолчанию 1,000,000 (млн).
    Возвращает множитель для приведения к миллионам.
    """
    if filename in SCALE_OVERRIDE:
        return SCALE_OVERRIDE[filename]

    val = get_val(df, 'Объем', col)
    if pd.isna(val) or val == 0:
        return 1.0  # default: данные уже в миллионах
    return val / 1_000_000


def parse_file(filepath, ticker_override=None, years_filter=None):
    filename = os.path.basename(filepath).replace('.xlsx', '')
    ticker = ticker_override if ticker_override else filename

    try:
        df = pd.read_excel(filepath, header=0, index_col=0)
    except Exception as e:
        print(f"  {filename}: ошибка чтения — {e}")
        return []

    cols = df.columns.tolist()

    # Валюта (одна на весь файл)
    currency = get_str(df, 'Валюта') or 'RUB'

    # Какой квартал годовой
    has_q4 = any('IV кв.' in str(c) for c in cols)
    target_q = 'IV кв.' if has_q4 else 'I кв.'

    results = []
    scales_log = []

    for col in cols:
        col_str = str(col).strip()
        if target_q not in col_str:
            continue

        try:
            year = int(col_str.split('.')[-1].strip())
        except:
            continue

        if year < 2018 or year > 2024:
            continue

        if years_filter is not None and year not in years_filter:
            continue

        # Масштаб для ЭТОГО столбца
        scale = get_column_scale(df, col, filename)
        scales_log.append((year, scale))

        row_data = {'ticker': ticker, 'year': year}

        for field, row_name in TARGET_ROWS.items():
            val = get_val(df, row_name, col)
            if pd.isna(val):
                row_data[field] = np.nan
                continue

            # Масштаб → млн единиц валюты
            val = val * scale

            # Конвертация в рубли
            if currency != 'RUB':
                rate_type = 'avg' if field in PNL_COLS else 'eoy'
                fx = get_fx(year, currency, rate_type)
                val = val * fx if not np.isnan(fx) else np.nan

            row_data[field] = val

        results.append(row_data)

    # Логируем если масштаб менялся между столбцами
    if len(scales_log) > 1:
        unique_scales = set(s for _, s in scales_log)
        if len(unique_scales) > 1:
            print(f"  ⚠️  {filename}: масштаб менялся между годами: "
                  f"{', '.join(f'{y}={s}' for y, s in scales_log)}")

    return results


# ── Основной цикл ─────────────────────────────────────────────────────────
all_data = []
files = sorted(glob.glob(os.path.join(DATA_DIR, "*.xlsx")))
valid_files = [f for f in files if not os.path.basename(f).startswith('~$')]

print(f"Найдено файлов: {len(valid_files)}")
print("=" * 60)

for filepath in valid_files:
    filename = os.path.basename(filepath).replace('.xlsx', '')

    if filename in SPECIAL_FILES:
        spec = SPECIAL_FILES[filename]
        rows = parse_file(filepath,
                          ticker_override=spec['ticker'],
                          years_filter=spec['years'])
        if rows:
            all_data.extend(rows)
            years = sorted([r['year'] for r in rows])
            print(f"{filename:20s} → {spec['ticker']:6s}: "
                  f"{len(rows)} лет ({min(years)}–{max(years)})")
        else:
            print(f"{filename:20s}: НЕТ ДАННЫХ")
        continue

    rows = parse_file(filepath)
    if rows:
        all_data.extend(rows)
        years = sorted([r['year'] for r in rows])
        print(f"{filename:20s} → {filename:6s}: "
              f"{len(rows)} лет ({min(years)}–{max(years)})")
    else:
        print(f"{filename:20s}: НЕТ ДАННЫХ")

# ── DataFrame ─────────────────────────────────────────────────────────────
df_out = pd.DataFrame(all_data)
df_out = df_out.sort_values(['ticker', 'year']).reset_index(drop=True)

# Убираем дубликаты (ticker+year), приоритет у основного файла (не _OLD)
df_out = df_out.drop_duplicates(subset=['ticker', 'year'], keep='first')

# ── debt_total = debt_short + debt_long где пусто ─────────────────────────
m_both  = df_out['debt_total'].isna() & df_out['debt_short'].notna() & df_out['debt_long'].notna()
m_short = df_out['debt_total'].isna() & df_out['debt_short'].notna() & df_out['debt_long'].isna()
m_long  = df_out['debt_total'].isna() & df_out['debt_short'].isna()  & df_out['debt_long'].notna()
df_out.loc[m_both,  'debt_total'] = df_out.loc[m_both,  'debt_short'] + df_out.loc[m_both, 'debt_long']
df_out.loc[m_short, 'debt_total'] = df_out.loc[m_short, 'debt_short']
df_out.loc[m_long,  'debt_total'] = df_out.loc[m_long,  'debt_long']

# ── Проверка скачков: находим фирмы где активы прыгают >100x ─────────────
print("\n" + "=" * 60)
print("ПРОВЕРКА СКАЧКОВ В ДАННЫХ (assets jump > 100x)")
print("=" * 60)

jumps_found = False
for t in df_out['ticker'].unique():
    sub = df_out[df_out['ticker'] == t].sort_values('year')
    assets = sub[['year', 'assets']].dropna()
    if len(assets) < 2:
        continue
    for i in range(len(assets) - 1):
        a1 = assets.iloc[i]['assets']
        a2 = assets.iloc[i + 1]['assets']
        y1 = int(assets.iloc[i]['year'])
        y2 = int(assets.iloc[i + 1]['year'])
        if a1 > 0 and a2 > 0:
            ratio = a1 / a2
            if ratio > 100 or ratio < 0.01:
                print(f"  ⚠️  {t}: {y1} assets={a1:,.0f} → "
                      f"{y2} assets={a2:,.0f} (ratio={ratio:.0f}x)")
                jumps_found = True

if not jumps_found:
    print("  ✅ Скачков не обнаружено")

# ── Сохраняем ─────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df_out.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 60)
print(f"Сохранено: {OUTPUT_FILE}")
print(f"Строк: {len(df_out)}, Компаний: {df_out['ticker'].nunique()}")

print("\nПроверка по годам:")
print(df_out.groupby('year')['ticker'].count())

# Проверяем проблемные фирмы
for t in ['SGZH', 'SMLT', 'GCHE', 'MSTT']:
    print(f"\nПроверка {t}:")
    sub = df_out[df_out['ticker'] == t][['year', 'assets', 'equity', 'debt_total', 'revenue']].sort_values('year')
    for _, r in sub.iterrows():
        print(f"  {int(r.year)}: assets={r.assets:>12,.0f}  equity={r.equity:>12,.0f}  "
              f"debt={r.debt_total:>12,.0f}  rev={r.revenue:>12,.0f}")

print("\nПроверка VKCO (ожидаем 2018–2024):")
print(df_out[df_out['ticker']=='VKCO'][['year','revenue','assets']].sort_values('year').to_string(index=False))

print("\nПроверка YDEX (ожидаем 2018–2024):")
print(df_out[df_out['ticker']=='YDEX'][['year','revenue','assets']].sort_values('year').to_string(index=False))

print("\nПроверка ROSN:")
print(df_out[df_out['ticker']=='ROSN'][['year','revenue','assets']].sort_values('year').to_string(index=False))

print("\nКонвертированные компании 2024 (млн руб):")
for t in ['GMKN', 'RUAL', 'ENPG', 'FLOT', 'RASP', 'GEMC']:
    r = df_out[(df_out['ticker'] == t) & (df_out['year'] == 2024)]
    if not r.empty:
        print(f"  {t:6s}: выручка={r['revenue'].values[0]:>12,.0f} | "
              f"активы={r['assets'].values[0]:>12,.0f}")