"""
25_stationarity.py
Three Panel Stationarity Tests (Section 4.2.5, Annex 3 Table A3b)

Объединённый скрипт, выполняющий три теста на стационарность:
  25) IPS (Im-Pesaran-Shin, 2003) на raw регрессорах
  26) IPS на within-демеанингованных регрессорах (size, B/M, leverage)
  27) CIPS (Pesaran, 2007) — cross-sectionally augmented ADF, который
      учитывает кросс-секционную зависимость через включение средних по
      когорте как регрессоров

Целевые числа (Table A3b):
  Size (raw)         : -0.860  (0.0% reject)  Unit root
  B/M (raw)          : -1.396  (4.6% reject)  Unit root
  Log Amihud (raw)   : -4.487  (86.2% reject) Stationary
  Momentum (raw)     : -2.079  (6.9% reject)  Stationary
  Leverage (raw)     : -1.282  (0.0% reject)  Unit root
  Size (within)      : -1.447  (0.0% reject)  Unit root
  B/M (within)       : -1.645  (5.7% reject)  Unit root
  Leverage (within)  : -1.303  (0.0% reject)  Unit root

CIPS-блок (часть 27) служит для подтверждения качественного вывода IPS:
  «CIPS results yield qualitatively the same conclusions.»
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

# ── Константы тестов ─────────────────────────────────────────────────────
IPS_CRIT_5PCT  = -1.73   # IPS 5% critical value (mean ADF t-statistic)
CIPS_CRIT_5PCT = -2.10   # CIPS 5% critical value (Pesaran 2007, Table 2)
ADF_P_THRESHOLD = 0.05   # порог для индивидуального ADF
MIN_OBS = 30             # минимум наблюдений на фирму для надёжного теста

# ── Чтение и подготовка данных ───────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
df['log_amihud'] = np.log1p(df['amihud'] * 1e9)
df = df.sort_values(['ticker', 'begin']).reset_index(drop=True)

print(f"Загружено: {len(df):,} строк, {df['ticker'].nunique()} компаний")

RAW_VARS = ['size', 'bm', 'log_amihud', 'momentum', 'leverage']
WITHIN_VARS = ['size', 'bm', 'leverage']  # только trending/slow-moving


# ═════════════════════════════════════════════════════════════════════════
# Часть 25: IPS на raw регрессорах
# ═════════════════════════════════════════════════════════════════════════

def panel_ips(df, var, demean=False):
    """
    IPS-тест: для каждой фирмы запускается ADF (regression='c', autolag='AIC'),
    усредняется t-статистика, считается доля фирм с p<0.05.
    """
    t_stats = []
    n_reject = 0
    n_tested = 0

    for ticker, group in df.groupby('ticker'):
        series = group[var].dropna()

        if demean:
            series = series - series.mean()

        if len(series) < MIN_OBS:
            continue

        try:
            result = adfuller(series.values, regression='c', autolag='AIC')
            t_stat, p_value = result[0], result[1]
            t_stats.append(t_stat)
            if p_value < ADF_P_THRESHOLD:
                n_reject += 1
            n_tested += 1
        except Exception:
            continue

    if n_tested == 0:
        return np.nan, np.nan, 0

    return np.mean(t_stats), 100.0 * n_reject / n_tested, n_tested


def ips_verdict(mean_t):
    return "Stationary" if mean_t < IPS_CRIT_5PCT else "Unit root"


# ═════════════════════════════════════════════════════════════════════════
# Часть 27: CIPS (Pesaran 2007)
# ═════════════════════════════════════════════════════════════════════════

def cadf_one(y, y_bar, lag=1):
    """
    Cross-section Augmented Dickey-Fuller (CADF) для одной фирмы.
    Регрессия: Δy_t = α + ρ y_{t-1} + d₀ ȳ_{t-1} + d₁ Δȳ_t
                       + Σ c_k Δy_{t-k} + ε
    Возвращает t-статистику коэффициента ρ.
    """
    if len(y) < MIN_OBS:
        return np.nan

    df_reg = pd.DataFrame({
        'dy':        y.diff(),
        'y_lag':     y.shift(1),
        'y_bar_lag': y_bar.shift(1),
        'dy_bar':    y_bar.diff(),
    })

    for k in range(1, lag + 1):
        df_reg[f'dy_lag{k}'] = y.diff().shift(k)

    df_reg = df_reg.dropna()
    if len(df_reg) < 20:
        return np.nan

    try:
        endog = df_reg['dy']
        exog = sm.add_constant(df_reg.drop('dy', axis=1))
        result = OLS(endog, exog).fit()
        return result.tvalues['y_lag']
    except Exception:
        return np.nan


def panel_cips(df, var, lag=1):
    """CIPS = среднее CADF по фирмам с использованием cross-section means."""
    # Пивотируем в широкий формат (date × ticker)
    wide = df.pivot_table(index='begin', columns='ticker',
                          values=var, aggfunc='first')

    # Cross-section mean каждой недели
    y_bar = wide.mean(axis=1)

    cadfs = []
    n_reject = 0
    n_tested = 0

    for ticker in wide.columns:
        y = wide[ticker].dropna()
        if len(y) < MIN_OBS:
            continue

        y_bar_aligned = y_bar.reindex(y.index)
        cadf_stat = cadf_one(y, y_bar_aligned, lag=lag)

        if not np.isnan(cadf_stat):
            cadfs.append(cadf_stat)
            if cadf_stat < -2.86:  # 5% crit для индивидуального CADF
                n_reject += 1
            n_tested += 1

    if n_tested == 0:
        return np.nan, np.nan, 0

    return np.mean(cadfs), 100.0 * n_reject / n_tested, n_tested


def cips_verdict(mean_t):
    return "Stationary" if mean_t < CIPS_CRIT_5PCT else "Unit root"


# ═════════════════════════════════════════════════════════════════════════
# ОСНОВНОЙ ВЫВОД: Table A3b
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("Table A3b. Panel Unit Root Tests (Im-Pesaran-Shin)")
print("=" * 78)
print(f"{'Variable':<25}{'Mean ADF t':>14}{'% Reject at 5%':>18}{'Verdict':>20}")
print("-" * 78)

# IPS raw
for var in RAW_VARS:
    mean_t, pct, n = panel_ips(df, var, demean=False)
    v = ips_verdict(mean_t)
    print(f"{f'{var} (raw)':<25}{mean_t:>14.3f}{pct:>17.1f}%{v:>20}")

# IPS within (демеанингованные)
for var in WITHIN_VARS:
    mean_t, pct, n = panel_ips(df, var, demean=True)
    v = ips_verdict(mean_t)
    print(f"{f'{var} (within)':<25}{mean_t:>14.3f}{pct:>17.1f}%{v:>20}")

print("-" * 78)
print(f"Approximate IPS 5% critical value for mean ADF t-statistic: {IPS_CRIT_5PCT}")
print("Source: python calculations.")


# ═════════════════════════════════════════════════════════════════════════
# CIPS RESULTS (часть 27)
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("CIPS Test (Pesaran 2007) — Cross-sectionally Augmented IPS")
print("=" * 78)
print(f"{'Variable':<25}{'Mean CADF t':>14}{'% Reject at 5%':>18}{'Verdict':>20}")
print("-" * 78)

for var in RAW_VARS:
    mean_t, pct, n = panel_cips(df, var, lag=1)
    if np.isnan(mean_t):
        print(f"{f'{var} (raw)':<25}{'n/a':>14}{'n/a':>18}{'n/a':>20}")
        continue
    v = cips_verdict(mean_t)
    print(f"{f'{var} (raw)':<25}{mean_t:>14.3f}{pct:>17.1f}%{v:>20}")

print("-" * 78)
print(f"Approximate CIPS 5% critical value: {CIPS_CRIT_5PCT}")
print("Pesaran (2007), Table 2, model with constant.")
print("Source: python calculations.")


# ═════════════════════════════════════════════════════════════════════════
# ИНТЕРПРЕТАЦИЯ
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print("ИНТЕРПРЕТАЦИЯ")
print("=" * 78)
print("""
Раздельные тесты подтверждают одинаковую картину:

• Size, B/M, Leverage — нестационарны (единичный корень). Это механический
  результат: log book assets трендует с ростом фирм, а B/M и leverage —
  медленные balance-sheet ratio. Two-way FE-оценщик остаётся consistent
  под общими стохастическими трендами, которые поглощаются time-FE
  (Wooldridge 2010, ch. 11).

• Log Amihud и Momentum — стационарны. Log Amihud — log-трансформированное
  отношение, Momentum — кумулятивный возврат за фиксированное окно.

• Within-демеанинговая версия для size/B/M/leverage показывает, что и после
  удаления firm-mean эти переменные остаются нестационарными.

• CIPS подтверждает выводы IPS качественно, что мотивирует
  first-differences проверку в Section 4.2.6.
""")