"""
29_placebo_tests.py
Placebo Break Date Tests (Section 4.2.7, Table 6)

Идея:
  Чтобы проверить, что коэффициенты δ отражают именно структурный сдвиг
  24 февраля 2022, а не общую нестабильность факторных премий, ограничиваем
  выборку только pre-break периодом (Jan 2020 — Feb 2022) и тестируем
  три "ложные" даты разрыва внутри него:
      1 Jun 2020, 1 Jan 2021, 1 Jun 2021.
  Для каждой строится тот же набор Post×Factor взаимодействий.
  Также для сравнения приводится actual break (24 Feb 2022) на полной выборке.

Целевые числа (Table 6):
   Break Date              Post×Size   Post×B/M    Post×LogAmih  Post×Leverage
   1 Jun 2020 (placebo)    -0.0015*    +0.0011     -0.0066***    -0.0032
   1 Jan 2021 (placebo)    -0.0012**   +0.0006     -0.0055***    -0.0077
   1 Jun 2021 (placebo)    -0.0019***  +0.0014     -0.0051***    -0.0128
   24 Feb 2022 (actual)    -0.0005     +0.0026***  -0.0026*      -0.0097**
"""

import numpy as np
import pandas as pd
from linearmodels import PanelOLS
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

# ── Константы ────────────────────────────────────────────────────────────
ACTUAL_BREAK = pd.Timestamp('2022-02-24')
PRE_BREAK_END = ACTUAL_BREAK  # граница pre-break выборки для placebo

PLACEBO_DATES = {
    '1 Jun 2020 (placebo)':  pd.Timestamp('2020-06-01'),
    '1 Jan 2021 (placebo)':  pd.Timestamp('2021-01-01'),
    '1 Jun 2021 (placebo)':  pd.Timestamp('2021-06-01'),
}

VARS_BASE = ['size', 'bm', 'log_amihud', 'momentum', 'leverage']
VARS_INTERACT = ['post_size', 'post_bm', 'post_log_amihud', 'post_leverage']
VARS = VARS_BASE + VARS_INTERACT


# ── Утилиты ──────────────────────────────────────────────────────────────
def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))


def stars(p):
    if p < 0.01: return '***'
    if p < 0.05: return '**'
    if p < 0.10: return '*'
    return ''


def prepare(df, break_date, restrict_to_pre=False):
    """
    Готовит данные для регрессии:
      1) log-transform Amihud
      2) если restrict_to_pre=True — оставляет только begin < ACTUAL_BREAK
      3) переустанавливает Post относительно переданной даты
      4) винсоризация 1/99 → создание interactions → set_index → dropna
    """
    d = df.copy()
    d['log_amihud'] = np.log1p(d['amihud'] * 1e9)

    if restrict_to_pre:
        d = d[d['begin'] < PRE_BREAK_END].copy()

    d['post'] = (d['begin'] >= break_date).astype(int)

    for col in ['ret'] + VARS_BASE:
        d[col] = winsorize(d[col])

    d['post_size']       = d['post'] * d['size']
    d['post_bm']         = d['post'] * d['bm']
    d['post_log_amihud'] = d['post'] * d['log_amihud']
    d['post_leverage']   = d['post'] * d['leverage']

    d = d.set_index(['ticker', 'begin'])
    return d[['ret'] + VARS].dropna()


def run_one(df, break_date, restrict_to_pre):
    """Запускает PanelOLS на подготовленных данных и возвращает результат."""
    panel = prepare(df, break_date, restrict_to_pre=restrict_to_pre)
    mod = PanelOLS(panel['ret'], panel[VARS],
                   entity_effects=True, time_effects=True,
                   drop_absorbed=True)
    return mod.fit(cov_type='clustered', cluster_entity=True), panel


# ── Загружаем сырую панель ───────────────────────────────────────────────
df_raw = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
print(f"Загружено: {len(df_raw):,} строк, {df_raw['ticker'].nunique()} компаний")


# ═════════════════════════════════════════════════════════════════════════
# Table 6. Placebo Break Date Tests
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("Table 6. Placebo Break Date Tests")
print("=" * 78)
print(f"\n{'Break Date':<24}{'Post×Size':>14}{'Post×B/M':>14}"
      f"{'Post×LogAmih':>16}{'Post×Leverage':>14}")
print("-" * 78)

all_results = {}

# ── Три плацебо-даты на pre-break выборке ────────────────────────────────
for label, bdate in PLACEBO_DATES.items():
    res, panel = run_one(df_raw, bdate, restrict_to_pre=True)
    all_results[label] = (res, len(panel))

    ps = f"{res.params['post_size']:+.4f}{stars(res.pvalues['post_size'])}"
    pb = f"{res.params['post_bm']:+.4f}{stars(res.pvalues['post_bm'])}"
    pa = f"{res.params['post_log_amihud']:+.4f}{stars(res.pvalues['post_log_amihud'])}"
    pl = f"{res.params['post_leverage']:+.4f}{stars(res.pvalues['post_leverage'])}"

    print(f"{label:<24}{ps:>14}{pb:>14}{pa:>16}{pl:>14}")

# ── Actual break на полной выборке (для сравнения) ───────────────────────
res_actual, panel_actual = run_one(df_raw, ACTUAL_BREAK, restrict_to_pre=False)
all_results['24 Feb 2022 (actual)'] = (res_actual, len(panel_actual))

ps = f"{res_actual.params['post_size']:+.4f}{stars(res_actual.pvalues['post_size'])}"
pb = f"{res_actual.params['post_bm']:+.4f}{stars(res_actual.pvalues['post_bm'])}"
pa = f"{res_actual.params['post_log_amihud']:+.4f}{stars(res_actual.pvalues['post_log_amihud'])}"
pl = f"{res_actual.params['post_leverage']:+.4f}{stars(res_actual.pvalues['post_leverage'])}"

print(f"{'24 Feb 2022 (actual)':<24}{ps:>14}{pb:>14}{pa:>16}{pl:>14}")

print("-" * 78)
print("*** p<0.01, ** p<0.05, * p<0.10. Source: python calculations.")


# ── Подробный вывод по каждой спецификации ───────────────────────────────
print("\n" + "=" * 78)
print("ПОДРОБНЫЕ РЕЗУЛЬТАТЫ ПО КАЖДОЙ ДАТЕ")
print("=" * 78)

for label, (res, n) in all_results.items():
    print(f"\n── {label} ──  N = {n:,}, R²-within = {res.rsquared:.4f}")
    print(f"{'Переменная':<22} {'Коэф.':>10} {'SE':>10} "
          f"{'t-stat':>8} {'p-value':>8}  ")
    print("-" * 65)
    for v in VARS_INTERACT:
        coef = res.params[v]
        se = res.std_errors[v]
        t = res.tstats[v]
        p = res.pvalues[v]
        print(f"{v:<22} {coef:>+10.4f} {se:>10.4f} "
              f"{t:>+8.3f} {p:>8.4f} {stars(p)}")


# ── Интерпретация ────────────────────────────────────────────────────────
print("\n" + "=" * 78)
print("ИНТЕРПРЕТАЦИЯ")
print("=" * 78)
print("""
Главный результат: Post × B/M значим только при actual break (24 Feb 2022),
во всех трёх плацебо-датах он статистически неотличим от нуля. Это сильное
эмпирическое подтверждение, что post-2022 реактивация value-премии
специфична для события февраля 2022, а не отражает общий дрейф.

Post × Leverage больше по магнитуде в actual, чем в большинстве плацебо,
что поддерживает break-специфичную идентификацию для H4.

Post × Log Amihud показывает обратную картину: плацебо-коэффициенты
превышают actual по абсолютной величине. Это указывает на ранее начавшийся
дрейф ликвидности (COVID 2020–2021), а не на эффект, уникально вызванный
санкциями. H3 квалифицируется соответственно (см. Section 5.3).
""")