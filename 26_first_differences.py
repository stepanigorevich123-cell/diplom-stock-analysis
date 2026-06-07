"""
26_first_differences.py
52-week First-Differences Robustness (Section 4.2.6, Table 5)

Спецификация:
  Медленные регрессоры (size, bm, leverage) входят как 52-недельные
  первые разности: Δ52 X_{i,t} = X_{i,t} - X_{i,t-52}.
  Log Amihud и momentum остаются в уровнях.
  
  Та же 1%/99% винсоризация, та же two-way FE структура,
  те же clustered SE по фирмам.

Целевые числа (Table 5):
  Post × Δ52 Size      = -0.0002 (p = 0.87)
  Post × Δ52 B/M       = +0.0051 (p = 0.001)
  Post × Δ52 Log Amih  = +0.0005 (p = 0.66)
  Post × Δ52 Leverage  = -0.0154 (p = 0.19)
  N = 20,431
  R²-within = 1.62%
"""

import numpy as np
import pandas as pd
from linearmodels import PanelOLS
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

# ── 1. Загружаем панель ──────────────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
df['log_amihud'] = np.log1p(df['amihud'] * 1e9)
df = df.sort_values(['ticker', 'begin']).reset_index(drop=True)
print(f"Загружено: {len(df):,} строк, {df['ticker'].nunique()} компаний")

# ── 2. 52-недельные первые разности по медленным регрессорам ─────────────
# Δ52 X_{i,t} = X_{i,t} - X_{i,t-52} внутри каждой фирмы
SLOW_VARS = ['size', 'bm', 'leverage']

for var in SLOW_VARS:
    df[f'd52_{var}'] = df.groupby('ticker')[var].diff(52)

# Log Amihud и momentum оставляем в уровнях (они уже стационарны)
# Это соответствует Section 4.2.6: "Log Amihud and momentum keep their level form"

# ── 3. Винсоризация 1%/99% (до создания interactions) ────────────────────
def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))

WINSOR_COLS = ['ret', 'd52_size', 'd52_bm', 'd52_leverage',
               'log_amihud', 'momentum']
for col in WINSOR_COLS:
    df[col] = winsorize(df[col])

# ── 4. Создание interaction terms (после винсоризации) ───────────────────
df['post_d52_size']    = df['post'] * df['d52_size']
df['post_d52_bm']      = df['post'] * df['d52_bm']
df['post_log_amihud']  = df['post'] * df['log_amihud']
df['post_d52_leverage']= df['post'] * df['d52_leverage']

# ── 5. Индекс панели и формирование выборки ──────────────────────────────
df = df.set_index(['ticker', 'begin'])

VARS = ['d52_size', 'd52_bm', 'log_amihud', 'momentum', 'd52_leverage',
        'post_d52_size', 'post_d52_bm', 'post_log_amihud',
        'post_d52_leverage']

df_fd = df[['ret'] + VARS].dropna()

print(f"\nПосле 52-week diff и dropna: {len(df_fd):,} наблюдений, "
      f"{df_fd.index.get_level_values('ticker').nunique()} компаний")
print(f"Pre-period:  {(df_fd.index.get_level_values('begin') < '2022-02-24').sum():,}")
print(f"Post-period: {(df_fd.index.get_level_values('begin') >= '2022-02-24').sum():,}")

# ── 6. Регрессия two-way FE с clustered SE ───────────────────────────────
print("\n" + "=" * 70)
print("FIRST-DIFFERENCES REGRESSION (Table 5)")
print("=" * 70)

mod = PanelOLS(df_fd['ret'], df_fd[VARS],
               entity_effects=True, time_effects=True,
               drop_absorbed=True)
res = mod.fit(cov_type='clustered', cluster_entity=True)

print(res.summary.tables[1])


# ── 7. Красивая итоговая таблица ─────────────────────────────────────────
def stars(p):
    if p < 0.01: return '***'
    if p < 0.05: return '**'
    if p < 0.10: return '*'
    return ''

print("\n" + "=" * 70)
print("ИТОГОВАЯ ТАБЛИЦА (First-Differences, Δ52)")
print("=" * 70)
print(f"\n{'Переменная':<25} {'Коэф.':>12} {'Std.Err.':>10} "
      f"{'t-stat':>8} {'p-value':>8} {'':>5}")
print("-" * 70)

display_names = {
    'd52_size':            'Δ52 Size',
    'd52_bm':              'Δ52 B/M',
    'log_amihud':          'Log Amihud',
    'momentum':            'Momentum',
    'd52_leverage':        'Δ52 Leverage',
    'post_d52_size':       'Post × Δ52 Size',
    'post_d52_bm':         'Post × Δ52 B/M',
    'post_log_amihud':     'Post × Log Amihud',
    'post_d52_leverage':   'Post × Δ52 Leverage',
}

for v in VARS:
    coef = res.params[v]
    se = res.std_errors[v]
    t = res.tstats[v]
    p = res.pvalues[v]
    name = display_names.get(v, v)
    print(f"{name:<25} {coef:>12.4f} {se:>10.4f} {t:>8.3f} "
          f"{p:>8.4f} {stars(p):>5}")

print("-" * 70)
print(f"\nR² (within):     {res.rsquared:.4f}")
print(f"N наблюдений:    {len(df_fd):,}")
print(f"N компаний:      {df_fd.index.get_level_values('ticker').nunique()}")
print(f"\n*** p<0.01, ** p<0.05, * p<0.10")