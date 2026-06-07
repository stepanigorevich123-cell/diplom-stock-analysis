import pandas as pd
import numpy as np
from linearmodels import PanelOLS, RandomEffects
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

# ── Загружаем и готовим данные ───────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])

VARS_BASE = ['size', 'bm', 'log_amihud', 'momentum', 'leverage']
VARS_INTERACT = ['post_size', 'post_bm', 'post_log_amihud', 'post_leverage']
VARS = VARS_BASE + VARS_INTERACT

def winsorize(series, lower=0.01, upper=0.99):
    return series.clip(series.quantile(lower), series.quantile(upper))

def prepare(df, lower=0.01, upper=0.99):
    """Correct order: log-transform → winsorize base → create interactions."""
    d = df.copy()
    d['log_amihud'] = np.log1p(d['amihud'] * 1e9)
    for col in ['ret'] + VARS_BASE:
        d[col] = winsorize(d[col], lower, upper)
    d['post_size']       = d['post'] * d['size']
    d['post_bm']         = d['post'] * d['bm']
    d['post_log_amihud'] = d['post'] * d['log_amihud']
    d['post_leverage']   = d['post'] * d['leverage']
    d = d.set_index(['ticker', 'begin'])
    return d[['ret'] + VARS + ['post']].dropna()

df_main = prepare(df)
print(f"Основная выборка: {len(df_main):,} наблюдений, "
      f"{df_main.index.get_level_values('ticker').nunique()} компаний")

def stars(p):
    if p < 0.01: return '***'
    if p < 0.05: return '**'
    if p < 0.10: return '*'
    return ''

# ═════════════════════════════════════════════════════════════════════════
# 1. ТЕСТ ХАУСМАНА (FE vs RE)
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("1. ТЕСТ ХАУСМАНА (Fixed Effects vs Random Effects)")
print("="*65)

fe_mod = PanelOLS(df_main['ret'], df_main[VARS],
                  entity_effects=True, time_effects=True)
re_mod = RandomEffects(df_main['ret'], df_main[VARS])

fe_res = fe_mod.fit(cov_type='clustered', cluster_entity=True)
re_res = re_mod.fit(cov_type='clustered', cluster_entity=True)

b_fe = fe_res.params
b_re = re_res.params
common = b_fe.index.intersection(b_re.index)
diff = b_fe[common] - b_re[common]

V_fe = fe_res.cov.loc[common, common]
V_re = re_res.cov.loc[common, common]
V_diff = V_fe - V_re

try:
    chi2 = float(diff @ np.linalg.inv(V_diff.values) @ diff)
    df_chi2 = len(common)
    p_hausman = 1 - stats.chi2.cdf(chi2, df_chi2)
    print(f"Chi² = {chi2:.4f}, df = {df_chi2}, p-value = {p_hausman:.4f}")
    if chi2 < 0:
        print("→ Отрицательная chi² — матрица разности вырождена (известная "
              "проблема с clustered SE). FE предпочтителен теоретически.")
    elif p_hausman < 0.05:
        print("→ Отвергаем RE, используем FE ✅")
    else:
        print("→ RE формально предпочтительнее, но FE более консервативен")
except:
    print("Матрица вырождена — тест не применим. "
          "FE предпочтителен теоретически ✅")

# ═════════════════════════════════════════════════════════════════════════
# 2. ТЕСТ НА ГЕТЕРОСКЕДАСТИЧНОСТЬ (Breusch-Pagan)
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("2. ТЕСТ BREUSCH-PAGAN НА ГЕТЕРОСКЕДАСТИЧНОСТЬ")
print("="*65)

resids = fe_res.resids.values
fitted = fe_res.fitted_values.values

X_bp = sm.add_constant(fitted)
resid_sq = resids ** 2
bp_model = sm.OLS(resid_sq, X_bp).fit()
bp_stat = len(resids) * bp_model.rsquared
bp_p = 1 - stats.chi2.cdf(bp_stat, 1)

print(f"BP statistic = {bp_stat:.4f}, p-value = {bp_p:.4f}")
if bp_p < 0.05:
    print("→ Гетероскедастичность обнаружена — кластеризованные SE необходимы ✅")
else:
    print("→ Гетероскедастичность не обнаружена на уровне fitted values")

# ═════════════════════════════════════════════════════════════════════════
# 3. ТЕСТ ЧОУ (структурный сдвиг 24.02.2022)
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("3. ТЕСТ ЧОУ (структурный сдвиг 24.02.2022)")
print("="*65)

BREAK_DATE = pd.Timestamp('2022-02-24')
BASIC_VARS = ['size', 'bm', 'log_amihud', 'momentum', 'leverage']

pre  = df_main[df_main.index.get_level_values('begin') < BREAK_DATE]
post = df_main[df_main.index.get_level_values('begin') >= BREAK_DATE]

def fit_fe(data, vlist=BASIC_VARS):
    mod = PanelOLS(data['ret'], data[vlist],
                   entity_effects=True, time_effects=True)
    return mod.fit(cov_type='clustered', cluster_entity=True)

full_res = fit_fe(df_main)
pre_res  = fit_fe(pre)
post_res = fit_fe(post)

rss_full = float((full_res.resids ** 2).sum())
rss_pre  = float((pre_res.resids ** 2).sum())
rss_post = float((post_res.resids ** 2).sum())
rss_restricted = rss_pre + rss_post

k = len(BASIC_VARS)
n = len(df_main)

chow_stat = ((rss_full - rss_restricted) / k) / (rss_restricted / (n - 2*k))
chow_p = 1 - stats.f.cdf(chow_stat, k, n - 2*k)

print(f"Chow F-stat = {chow_stat:.4f}, p-value = {chow_p:.6f}")
print(f"Pre-period:  {len(pre):,} наблюдений")
print(f"Post-period: {len(post):,} наблюдений")
if chow_p < 0.05:
    print("→ Структурный сдвиг подтверждён ✅")
else:
    print("→ Структурный сдвиг не обнаружен")

# ═════════════════════════════════════════════════════════════════════════
# 4. МУЛЬТИКОЛЛИНЕАРНОСТЬ (VIF)
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("4. VIF (мультиколлинеарность)")
print("="*65)

X_vif = df_main[VARS].copy()
vif_results = []
for col in VARS:
    y = X_vif[col]
    X = sm.add_constant(X_vif.drop(columns=[col]))
    r2 = sm.OLS(y, X).fit().rsquared
    vif = 1 / (1 - r2) if r2 < 1 else np.inf
    vif_results.append((col, vif))
    status = "⚠️ ВЫСОКИЙ" if vif > 10 else "✅ OK"
    print(f"  {col:<20}: VIF = {vif:.2f}  {status}")

# ═════════════════════════════════════════════════════════════════════════
# 5. FAMA-MACBETH РЕГРЕССИЯ
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("5. FAMA-MACBETH РЕГРЕССИЯ")
print("="*65)

df_fm = df_main.reset_index()

weeks = sorted(df_fm['begin'].unique())
fm_coefs = []

for week in weeks:
    week_data = df_fm[df_fm['begin'] == week].dropna(subset=['ret'] + VARS)
    if len(week_data) < 20:
        continue
    try:
        X = sm.add_constant(week_data[VARS])
        y = week_data['ret']
        res_fm = sm.OLS(y, X).fit()
        coefs = res_fm.params.to_dict()
        coefs['week'] = week
        fm_coefs.append(coefs)
    except:
        continue

fm_df = pd.DataFrame(fm_coefs).drop(columns=['week', 'const'], errors='ignore')
fm_means = fm_df.mean()
fm_se    = fm_df.std() / np.sqrt(len(fm_df))
fm_t     = fm_means / fm_se
fm_p     = pd.Series(
    2 * (1 - stats.t.cdf(np.abs(fm_t.values), df=len(fm_df)-1)),
    index=fm_means.index
)

print(f"Количество недельных регрессий: {len(fm_df)}")
print(f"\n{'Переменная':<20} {'Коэф.':>12} {'SE':>10} {'t-stat':>8} {'p-value':>8} {'':>5}")
print("-"*65)
for v in VARS:
    if v in fm_means.index:
        print(f"{v:<20} {fm_means[v]:>12.6f} {fm_se[v]:>10.6f} "
              f"{fm_t[v]:>8.3f} {float(fm_p[v]):>8.4f} "
              f"{stars(float(fm_p[v])):>5}")

# ═════════════════════════════════════════════════════════════════════════
# 6. WINSORIZATION 2.5%-97.5%
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("6. ROBUSTNESS: Winsorization 2.5%-97.5%")
print("="*65)

df_w25 = prepare(df, lower=0.025, upper=0.975)
mod_w25 = PanelOLS(df_w25['ret'], df_w25[VARS],
                   entity_effects=True, time_effects=True)
res_w25 = mod_w25.fit(cov_type='clustered', cluster_entity=True)

print(f"Наблюдений: {len(df_w25):,}")
print(f"\n{'Переменная':<20} {'1%-99%':>12} {'p':>8} {'2.5%-97.5%':>12} {'p':>8} {'Знак':>5}")
print("-"*68)
for v in VARS:
    c1 = fe_res.params[v]
    p1 = fe_res.pvalues[v]
    c2 = res_w25.params[v]
    p2 = res_w25.pvalues[v]
    chg = "✅" if np.sign(c1) == np.sign(c2) else "⚠️"
    print(f"{v:<20} {c1:>10.4f}{stars(p1):<3} {p1:>6.4f} "
          f"{c2:>10.4f}{stars(p2):<3} {p2:>6.4f} {chg:>5}")

# ═════════════════════════════════════════════════════════════════════════
# 7. РАЗНЫЕ ДАТЫ РАЗРЫВА
# ═════════════════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("7. ROBUSTNESS: Разные даты разрыва")
print("="*65)

break_dates = {
    '01.01.2022': pd.Timestamp('2022-01-01'),
    '24.02.2022': pd.Timestamp('2022-02-24'),
    '01.04.2022': pd.Timestamp('2022-04-01'),
    '01.07.2022': pd.Timestamp('2022-07-01'),
}

print(f"\n{'Дата разрыва':<15} {'Post×Size':>12} {'Post×BM':>12} "
      f"{'Post×LogAmih':>14} {'Post×Lev':>12}")
print("-"*68)
for label, bdate in break_dates.items():
    d = df.copy()
    d['post'] = (pd.to_datetime(d['begin']) >= bdate).astype(int)
    try:
        d2 = prepare(d)
        m = PanelOLS(d2['ret'], d2[VARS],
                     entity_effects=True, time_effects=True)
        r = m.fit(cov_type='clustered', cluster_entity=True)
        ps = f"{r.params['post_size']:.4f}{stars(r.pvalues['post_size'])}"
        pb = f"{r.params['post_bm']:.4f}{stars(r.pvalues['post_bm'])}"
        pa = f"{r.params['post_log_amihud']:.4f}{stars(r.pvalues['post_log_amihud'])}"
        pl = f"{r.params['post_leverage']:.4f}{stars(r.pvalues['post_leverage'])}"
        print(f"{label:<15} {ps:>12} {pb:>12} {pa:>14} {pl:>12}")
    except Exception as e:
        print(f"{label:<15} ошибка: {e}")

print("\n*** p<0.01, ** p<0.05, * p<0.10")
print("\nВсе тесты завершены!")