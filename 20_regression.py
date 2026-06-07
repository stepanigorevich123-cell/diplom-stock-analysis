import pandas as pd
import numpy as np
from linearmodels import PanelOLS
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

# ── 1. Загружаем панель ───────────────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
print(f"Загружено: {len(df)} строк, {df['ticker'].nunique()} компаний")

# ── 2. Log-трансформация Amihud ──────────────────────────────────────────
# Amihud имеет экстремально правый хвост. Log сжимает его без
# искусственного клиппинга. Множитель 1e9 приводит значения к удобной шкале.
df['log_amihud'] = np.log1p(df['amihud'] * 1e9)

# ── 3. Winsorize BASE variables FIRST ────────────────────────────────────
# Критично: винсоризация базовых переменных ДО создания interactions,
# чтобы post_X = post * X_winsorized (а не winsorize(post * X) отдельно).
def winsorize(series, lower=0.01, upper=0.99):
    q_low  = series.quantile(lower)
    q_high = series.quantile(upper)
    return series.clip(q_low, q_high)

for col in ['ret', 'size', 'bm', 'leverage', 'log_amihud', 'momentum']:
    df[col] = winsorize(df[col])

# ── 4. THEN create interaction terms ─────────────────────────────────────
df['post_size']       = df['post'] * df['size']
df['post_bm']         = df['post'] * df['bm']
df['post_log_amihud'] = df['post'] * df['log_amihud']
df['post_leverage']   = df['post'] * df['leverage']

# ── 5. Индекс панели ────────────────────────────────────────────────────
df = df.set_index(['ticker', 'begin'])

# ── 6. Основная регрессия ────────────────────────────────────────────────
print("\n" + "="*70)
print("ОСНОВНАЯ РЕГРЕССИЯ: log(1 + Amihud*1e9)")
print("="*70)

vars_main = ['size', 'bm', 'log_amihud', 'momentum', 'leverage',
             'post_size', 'post_bm', 'post_log_amihud', 'post_leverage']

df_main = df[['ret'] + vars_main].dropna()
print(f"Наблюдений: {len(df_main):,}, Компаний: {df_main.index.get_level_values('ticker').nunique()}")
print(f"Pre-period:  {(df_main.index.get_level_values('begin') < '2022-02-24').sum():,} наблюдений")
print(f"Post-period: {(df_main.index.get_level_values('begin') >= '2022-02-24').sum():,} наблюдений")

mod = PanelOLS(
    dependent      = df_main['ret'],
    exog           = df_main[vars_main],
    entity_effects = True,
    time_effects   = True,
)
res = mod.fit(cov_type='clustered', cluster_entity=True)

print(res.summary.tables[1])

# ── 7. Красивая итоговая таблица ─────────────────────────────────────────
print("\n" + "="*70)
print("ИТОГОВАЯ ТАБЛИЦА")
print("="*70)

def stars(p):
    if p < 0.01: return '***'
    if p < 0.05: return '**'
    if p < 0.10: return '*'
    return ''

labels = {
    'size':            'Size (log assets)',
    'bm':              'B/M ratio',
    'log_amihud':      'Log Amihud',
    'momentum':        'Momentum',
    'leverage':        'Leverage',
    'post_size':       'Post × Size',
    'post_bm':         'Post × B/M',
    'post_log_amihud': 'Post × Log Amihud',
    'post_leverage':   'Post × Leverage',
}

print(f"\n{'Переменная':<25} {'Коэф.':>12} {'Std.Err.':>10} {'t-stat':>8} {'p-value':>8} {'':>5}")
print("-"*70)
for v in vars_main:
    coef = res.params[v]
    se   = res.std_errors[v]
    t    = res.tstats[v]
    p    = res.pvalues[v]
    s    = stars(p)
    print(f"{labels[v]:<25} {coef:>12.6f} {se:>10.6f} {t:>8.3f} {p:>8.4f} {s:>5}")

print("-"*70)
print(f"\nR² (within):     {res.rsquared:.4f}")
print(f"N наблюдений:    {len(df_main):,}")
print(f"N компаний:      {df_main.index.get_level_values('ticker').nunique()}")
print(f"Firm FE:         Да")
print(f"Time FE:         Да")
print(f"Clustered SE:    По компании")
print(f"\n*** p<0.01, ** p<0.05, * p<0.10")