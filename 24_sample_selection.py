"""
24_sample_selection.py
Построение Table 1: Sample Selection
Последовательность фильтров: 260 → 117 → 87 → 21,741

Замечание: значения 260 (стартовый MOEX TQBR universe) и 117 (после фильтра
по истории цен) получены upstream в скриптах 01–07 при работе с raw MOEX API
и Cbonds matching, и не воспроизводятся из panel_data.csv напрямую.
В этом скрипте они зафиксированы как константы с комментариями. Финальные
строки (87 firms, 21,741 firm-week obs) считаются непосредственно из панели.
"""

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

# ── Константы из upstream-пайплайна (скрипты 01–07) ──────────────────────
N_INITIAL_UNIVERSE = 260   # MOEX TQBR common stocks по состоянию на 2026-02
N_AFTER_PRICE_FILTER = 117 # после фильтра ≥52 недель цены в одной из подвыборок
N_DROPPED_PRICES = N_INITIAL_UNIVERSE - N_AFTER_PRICE_FILTER  # 143
N_AFTER_CBONDS = 87        # после фильтра по Cbonds IFRS coverage
N_DROPPED_CBONDS = N_AFTER_PRICE_FILTER - N_AFTER_CBONDS      # 30

# ── Чтение финальной панели ──────────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
n_firms_final = df['ticker'].nunique()
n_obs_final = len(df)

assert n_firms_final == N_AFTER_CBONDS, (
    f"Несоответствие: в панели {n_firms_final} фирм, ожидалось {N_AFTER_CBONDS}"
)

# ── Вывод Table 1 ────────────────────────────────────────────────────────
print("=" * 78)
print("Table 1. Sample Selection")
print("=" * 78)
print(f"{'Filter applied':<55}{'N before':>10}{'N dropped':>10}{'N after':>10}")
print("-" * 78)

print(f"{'Initial MOEX TQBR universe':<55}"
      f"{'n/a':>10}{'n/a':>10}{N_INITIAL_UNIVERSE:>10}")

print(f"{'At least 52 weeks of price history in ≥1 subperiod':<55}"
      f"{N_INITIAL_UNIVERSE:>10}{N_DROPPED_PRICES:>10}"
      f"{N_AFTER_PRICE_FILTER:>10}")

print(f"{'Coverage in Cbonds IFRS fundamental database':<55}"
      f"{N_AFTER_PRICE_FILTER:>10}{N_DROPPED_CBONDS:>10}"
      f"{N_AFTER_CBONDS:>10}")

print(f"{'Final panel (firm-week obs with all regressors)':<55}"
      f"{'n/a':>10}{'n/a':>10}{n_obs_final:>10,}")

print("-" * 78)
print(f"Source: python calculations from 24_sample_selection.py")
print()
print(f"Контрольные значения из panel_data.csv:")
print(f"  N firms:    {n_firms_final}")
print(f"  N firm-weeks: {n_obs_final:,}")
print(f"  Период:     {df['begin'].min():%Y-%m-%d} — {df['begin'].max():%Y-%m-%d}")
print(f"  Pre-shock:  {(df['begin'] < '2022-02-24').sum():,} наблюдений")
print(f"  Post-shock: {(df['begin'] >= '2022-02-24').sum():,} наблюдений")