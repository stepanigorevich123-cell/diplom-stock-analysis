"""
29_portfolio_sorts.py
Long-Short Quintile Portfolio Sorts (Section 4.2.8, Table 7)

Идея:
  Для каждой характеристики (size, B/M, log Amihud, leverage) в каждую
  неделю t отсортируем 87 фирм на 5 квинтилей. Внутри каждого квинтиля
  считаем equal-weighted средний возврат за неделю. Long-short = разница
  средних возвратов крайних квинтилей в эту неделю. Направление long-short
  следует соответствующей гипотезе:
      Size:        Small − Big       (Q1 − Q5)
      B/M:         High − Low        (Q5 − Q1)
      Log Amihud:  Illiquid − Liquid (Q5 − Q1)
      Leverage:    Low − High        (Q1 − Q5)
  Получаем временной ряд недельных long-short возвратов, считаем средние
  до и после break (24 Feb 2022), аннуализируем (× 52). Welch t-test
  применяется к недельным возвратам pre vs post.

Целевые числа (Table 7):
  Size       Small − Big        +5.1%  → +22.0%   Δ +16.9 pp  p=0.265
  B/M        High − Low        −23.5%  →  −4.8%   Δ +18.6 pp  p=0.100
  Log Amih   Illiquid − Liquid +11.4%  → +24.6%   Δ +13.2 pp  p=0.459
  Leverage   Low − High        −23.9%  → +12.2%   Δ +36.1 pp  p=0.0005
"""

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"
ACTUAL_BREAK = pd.Timestamp('2022-02-24')
N_QUINTILES = 5
MIN_FIRMS_PER_WEEK = 10   # минимум фирм в неделю для надёжного quintile sort
ANNUALIZE = 52            # 52 недели в году

# ── Чтение и подготовка данных ───────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
df['log_amihud'] = np.log1p(df['amihud'] * 1e9)

# Винсоризация 1%/99% — согласуется с основной регрессией
def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))

for col in ['ret', 'size', 'bm', 'log_amihud', 'leverage']:
    df[col] = winsorize(df[col])

print(f"Загружено: {len(df):,} строк, {df['ticker'].nunique()} компаний")


# ── Функция построения недельных long-short возвратов ────────────────────
def build_long_short(df, char, direction):
    """
    Строит временной ряд недельных long-short квинтильных возвратов.

    direction: 'Q5_minus_Q1'  — top quintile − bottom quintile
               'Q1_minus_Q5'  — bottom − top
    """
    weekly_ls = {}

    for date, week in df.groupby('begin'):
        # Дроп NaN по characteristic и возврату
        week = week[['ret', char]].dropna()
        if len(week) < MIN_FIRMS_PER_WEEK:
            continue

        # Quintile sort. labels=False даёт 0..4
        try:
            week = week.copy()
            week['q'] = pd.qcut(week[char], N_QUINTILES,
                                labels=False, duplicates='drop')
        except ValueError:
            # Слишком мало уникальных значений для qcut — пропускаем неделю
            continue

        # Equal-weighted среднее по каждому квинтилю
        q_means = week.groupby('q')['ret'].mean()

        # Нужны крайние квинтили
        if 0 not in q_means.index or (N_QUINTILES - 1) not in q_means.index:
            continue

        top = q_means[N_QUINTILES - 1]
        bottom = q_means[0]

        if direction == 'Q5_minus_Q1':
            weekly_ls[date] = top - bottom
        elif direction == 'Q1_minus_Q5':
            weekly_ls[date] = bottom - top
        else:
            raise ValueError(f"Unknown direction: {direction}")

    return pd.Series(weekly_ls).sort_index()


# ── Функция сравнения pre vs post ────────────────────────────────────────
def compare_pre_post(ls_series, pre_end=ACTUAL_BREAK):
    """Возвращает аннуализированные средние и Welch t-test p-value."""
    pre = ls_series[ls_series.index < pre_end]
    post = ls_series[ls_series.index >= pre_end]

    pre_ann = pre.mean() * ANNUALIZE * 100   # в процентах годовых
    post_ann = post.mean() * ANNUALIZE * 100
    diff_pp = post_ann - pre_ann

    # Welch t-test (разные дисперсии в pre vs post)
    if len(pre) > 1 and len(post) > 1:
        t_stat, p_value = ttest_ind(pre, post, equal_var=False)
    else:
        t_stat, p_value = np.nan, np.nan

    return {
        'pre_ann':  pre_ann,
        'post_ann': post_ann,
        'diff_pp':  diff_pp,
        'p_value':  p_value,
        'n_pre':    len(pre),
        'n_post':   len(post),
    }


# ── Спецификации стратегий ───────────────────────────────────────────────
STRATEGIES = [
    # (label, characteristic, direction_code, direction_label)
    ('Size',       'size',       'Q1_minus_Q5', 'Small − Big'),
    ('B/M',        'bm',         'Q5_minus_Q1', 'High − Low'),
    ('Log Amihud', 'log_amihud', 'Q5_minus_Q1', 'Illiquid − Liquid'),
    ('Leverage',   'leverage',   'Q1_minus_Q5', 'Low − High'),
]


# ═════════════════════════════════════════════════════════════════════════
# ОСНОВНОЙ ВЫВОД: Table 7
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("Table 7. Long-Short Portfolio Returns, Pre-Shock vs Post-Shock")
print("=" * 78)
print(f"{'Characteristic':<14}{'Direction':<22}"
      f"{'Pre (ann.%)':>13}{'Post (ann.%)':>14}"
      f"{'Δ (pp)':>10}{'p-value':>10}")
print("-" * 78)

results = {}

for label, char, direction, dir_label in STRATEGIES:
    ls = build_long_short(df, char, direction)
    res = compare_pre_post(ls)
    results[label] = (ls, res)

    print(f"{label:<14}{dir_label:<22}"
          f"{res['pre_ann']:>+12.1f}%{res['post_ann']:>+13.1f}%"
          f"{res['diff_pp']:>+10.1f}{res['p_value']:>10.4f}")

print("-" * 78)
print("p-values from Welch t-test on difference of means. Source: python calculations.")


# ── Подробный вывод по каждой стратегии ──────────────────────────────────
print("\n" + "=" * 78)
print("ПОДРОБНЫЕ РЕЗУЛЬТАТЫ ПО КАЖДОЙ СТРАТЕГИИ")
print("=" * 78)

for label, char, direction, dir_label in STRATEGIES:
    ls, res = results[label]
    print(f"\n── {label} ({dir_label}) ──")
    print(f"  Pre-shock:  {res['n_pre']:>4} weeks, "
          f"weekly mean = {res['pre_ann']/52:+.4f}, "
          f"annualized = {res['pre_ann']:+.2f}%")
    print(f"  Post-shock: {res['n_post']:>4} weeks, "
          f"weekly mean = {res['post_ann']/52:+.4f}, "
          f"annualized = {res['post_ann']:+.2f}%")
    print(f"  Δ (annualized): {res['diff_pp']:+.2f} pp,  "
          f"Welch p-value = {res['p_value']:.4f}")


# ── Интерпретация ────────────────────────────────────────────────────────
print("\n" + "=" * 78)
print("ИНТЕРПРЕТАЦИЯ")
print("=" * 78)
print("""
Главные результаты:

• Leverage spread (Low − High) сдвигается с −24% до +12% годовых,
  свинг на +36 п.п. при p = 0.0005. Это крупнейший экономический эффект
  среди четырёх характеристик. Согласуется с регрессионным Post×Leverage
  и подтверждает гипотезу H4 (леверидж сменил роль премии на штраф).

• B/M spread (High − Low) сжимается с −23.5% до −4.8%, реактивация на
  +18.6 п.п. (p = 0.100). Согласуется с регрессионным Post×B/M = +0.0026***
  и H2 (value-штраф ослаб).

• Size spread (Small − Big) растёт с +5.1% до +22.0% (+16.9 п.п., p = 0.265).
  Не достигает конвенциональной значимости в t-тесте, но направленно
  согласуется с H1. Этот результат соответствует ровно тому измерению
  (between-firm), которое within-firm регрессия не идентифицирует (Section 3.7).

• Log Amihud spread (Illiquid − Liquid) расширяется с +11.4% до +24.6%
  (+13.2 п.п., p = 0.459). Незначим. Направленное противоречие с
  регрессионным знаком отражает разницу within-firm vs between-firm
  идентификации.
""")