import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

SECTORS = {
    # Нефть и газ (8)
    'GAZP': 'Нефть и газ', 'LKOH': 'Нефть и газ', 'NVTK': 'Нефть и газ',
    'TATN': 'Нефть и газ', 'SIBN': 'Нефть и газ', 'RNFT': 'Нефть и газ',
    'FLOT': 'Нефть и газ', 'NMTP': 'Нефть и газ',
    # Чёрная металлургия (7)
    'NLMK': 'Металлургия', 'CHMF': 'Металлургия', 'MAGN': 'Металлургия',
    'CHMK': 'Металлургия', 'AMEZ': 'Металлургия', 'BRZL': 'Металлургия', 'TRMK': 'Металлургия',
    # Цветная металлургия (8)
    'GMKN': 'Цветная металлургия', 'RUAL': 'Цветная металлургия', 'ENPG': 'Цветная металлургия',
    'VSMO': 'Цветная металлургия', 'ALRS': 'Цветная металлургия', 'PLZL': 'Цветная металлургия',
    'SELG': 'Цветная металлургия', 'UGLD': 'Цветная металлургия',
    # Электроэнергетика (18)
    'HYDR': 'Электроэнергетика', 'TGKB': 'Электроэнергетика', 'TGKN': 'Электроэнергетика',
    'ELFV': 'Электроэнергетика', 'IRAO': 'Электроэнергетика', 'FEES': 'Электроэнергетика',
    'MRKC': 'Электроэнергетика', 'MRKS': 'Электроэнергетика', 'MRKU': 'Электроэнергетика',
    'MRKV': 'Электроэнергетика', 'MRKY': 'Электроэнергетика', 'MRKZ': 'Электроэнергетика',
    'MSRS': 'Электроэнергетика', 'DVEC': 'Электроэнергетика', 'LSNG': 'Электроэнергетика',
    'VRSB': 'Электроэнергетика', 'KLSB': 'Электроэнергетика', 'EELT': 'Электроэнергетика',
    # Телеком и IT (9)
    'MTSS': 'Телеком и IT', 'RTKM': 'Телеком и IT', 'NSVZ': 'Телеком и IT',
    'YDEX': 'Телеком и IT', 'VKCO': 'Телеком и IT', 'POSI': 'Телеком и IT',
    'HEAD': 'Телеком и IT', 'ASTR': 'Телеком и IT', 'SOFL': 'Телеком и IT',
    # Ритейл (6)
    'MGNT': 'Ритейл', 'LENT': 'Ритейл', 'MVID': 'Ритейл',
    'X5': 'Ритейл', 'BELU': 'Ритейл', 'HNFG': 'Ритейл',
    # Химия и агро (6)
    'PHOR': 'Химия и агро', 'AKRN': 'Химия и агро', 'KAZT': 'Химия и агро',
    'KZOS': 'Химия и агро', 'NKNC': 'Химия и агро', 'NKHP': 'Химия и агро',
    # Транспорт (6)
    'AFLT': 'Транспорт', 'FESH': 'Транспорт', 'UWGN': 'Транспорт',
    'UNAC': 'Транспорт', 'GTRK': 'Транспорт', 'EUTR': 'Транспорт',
    # Девелопмент (3)
    'SMLT': 'Девелопмент', 'LSRG': 'Девелопмент', 'PIKK': 'Девелопмент',
    # Машиностроение (5)
    'KMAZ': 'Машиностроение', 'SVAV': 'Машиностроение', 'NFAZ': 'Машиностроение',
    'MSTT': 'Машиностроение', 'ZILL': 'Машиностроение',
    # Холдинги (2)
    'AFKS': 'Холдинги', 'LIFE': 'Холдинги',
    # Пищевая (3)
    'GCHE': 'Пищевая', 'ABRD': 'Пищевая', 'AQUA': 'Пищевая',
    # Лес и стройматериалы (2)
    'SGZH': 'Лес и стройматериалы', 'PRFN': 'Лес и стройматериалы',
    # Прочее (4)
    'ABIO': 'Прочее', 'GEMA': 'Прочее', 'KROT': 'Прочее', 'ROLO': 'Прочее',
}

assert len(SECTORS) == 87, f"Expected 87 tickers, got {len(SECTORS)}"

# ── Загружаем данные ─────────────────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
df['log_amihud'] = np.log1p(df['amihud'] * 1e9)
BREAK = pd.Timestamp('2022-02-24')

# Средние характеристики по компании за весь период
company_features = df.groupby('ticker').agg(
    size       = ('size',       'mean'),
    leverage   = ('leverage',   'mean'),
    bm         = ('bm',         'mean'),
    amihud     = ('amihud',     'mean'),
    log_amihud = ('log_amihud', 'mean'),
    ret_pre    = ('ret',        lambda x: x[df.loc[x.index, 'begin'] < BREAK].mean()),
    ret_post   = ('ret',        lambda x: x[df.loc[x.index, 'begin'] >= BREAK].mean()),
).dropna(subset=['size', 'leverage', 'bm'])

company_features['sector'] = company_features.index.map(SECTORS).fillna('Прочее')
company_features['ret_change'] = company_features['ret_post'] - company_features['ret_pre']

# ── K-means кластеризация ────────────────────────────────────────────────
# Используем log_amihud вместо raw amihud для консистентности с регрессией
CLUSTER_VARS = ['size', 'leverage', 'bm', 'log_amihud']
N_CLUSTERS = 4

X = company_features[CLUSTER_VARS].fillna(company_features[CLUSTER_VARS].median())
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
company_features['cluster'] = kmeans.fit_predict(X_scaled)

# ── Характеристики кластеров ─────────────────────────────────────────────
print("="*70)
print("K-MEANS КЛАСТЕРИЗАЦИЯ (4 кластера, log_amihud)")
print("="*70)

cluster_stats = company_features.groupby('cluster').agg(
    n          = ('size',       'count'),
    size       = ('size',       'mean'),
    leverage   = ('leverage',   'mean'),
    bm         = ('bm',         'mean'),
    log_amihud = ('log_amihud', 'mean'),
    ret_pre    = ('ret_pre',    'mean'),
    ret_post   = ('ret_post',   'mean'),
    ret_chg    = ('ret_change', 'mean'),
).round(3)

print(f"\n{'Кластер':<10} {'N':>3} {'Size':>6} {'Lev':>6} {'B/M':>6} "
      f"{'LogAmih':>8} {'Pre ret':>8} {'Post ret':>9} {'Изменение':>10}")
print("-"*75)
for cl, row in cluster_stats.iterrows():
    arrow = '↑' if row['ret_chg'] > 0 else '↓'
    print(f"{cl:<10} {int(row['n']):>3} {row['size']:>6.1f} "
          f"{row['leverage']:>6.2f} {row['bm']:>6.2f} "
          f"{row['log_amihud']:>8.2f} {row['ret_pre']:>8.4f} "
          f"{row['ret_post']:>9.4f} {row['ret_chg']:>+9.4f} {arrow}")

# ── Состав кластеров ─────────────────────────────────────────────────────
print("\n" + "="*70)
print("СОСТАВ КЛАСТЕРОВ")
print("="*70)

for cl in range(N_CLUSTERS):
    members = company_features[company_features['cluster'] == cl]
    members_sorted = members.sort_values('ret_post', ascending=False)

    print(f"\n{'─'*70}")
    print(f"КЛАСТЕР {cl} | {len(members)} компаний | Post ret: "
          f"{members['ret_post'].mean():+.4f} | Size: {members['size'].mean():.1f} "
          f"| B/M: {members['bm'].mean():.2f} | Lev: {members['leverage'].mean():.2f}")
    print(f"{'─'*70}")
    print(f"{'Тикер':<8} {'Сектор':<22} {'Pre':>8} {'Post':>8} {'Изменение':>10}")
    print("-"*60)
    for ticker, row in members_sorted.iterrows():
        print(f"{ticker:<8} {row['sector']:<22} {row['ret_pre']:>8.4f} "
              f"{row['ret_post']:>8.4f} {row['ret_change']:>+10.4f}")

# ── Секторный состав кластеров ───────────────────────────────────────────
print("\n" + "="*70)
print("СЕКТОРНЫЙ СОСТАВ КЛАСТЕРОВ")
print("="*70)

sector_cluster = pd.crosstab(
    company_features['sector'],
    company_features['cluster'],
    margins=True
)
print(sector_cluster.to_string())

print("\nГотово!")