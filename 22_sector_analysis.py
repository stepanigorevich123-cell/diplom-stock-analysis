import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

PANEL_FILE = r"D:\diplom\data\panel_data.csv"

# Секторная разметка 87 компаний — БЕЗ ДУБЛИКАТОВ
# Каждый тикер присвоен ровно одному сектору.
SECTORS = {
    # Нефть и газ (8)
    'GAZP': 'Нефть и газ', 'LKOH': 'Нефть и газ', 'NVTK': 'Нефть и газ',
    'TATN': 'Нефть и газ', 'SIBN': 'Нефть и газ', 'RNFT': 'Нефть и газ',
    'FLOT': 'Нефть и газ', 'NMTP': 'Нефть и газ',

    # Чёрная металлургия (7)
    'NLMK': 'Металлургия', 'CHMF': 'Металлургия', 'MAGN': 'Металлургия',
    'CHMK': 'Металлургия', 'AMEZ': 'Металлургия', 'BRZL': 'Металлургия',
    'TRMK': 'Металлургия',

    # Цветная металлургия (8)
    'GMKN': 'Цветная металлургия', 'RUAL': 'Цветная металлургия',
    'ENPG': 'Цветная металлургия', 'VSMO': 'Цветная металлургия',
    'ALRS': 'Цветная металлургия', 'PLZL': 'Цветная металлургия',
    'SELG': 'Цветная металлургия', 'UGLD': 'Цветная металлургия',

    # Электроэнергетика (18)
    'HYDR': 'Электроэнергетика', 'TGKB': 'Электроэнергетика',
    'TGKN': 'Электроэнергетика', 'ELFV': 'Электроэнергетика',
    'IRAO': 'Электроэнергетика', 'FEES': 'Электроэнергетика',
    'MRKC': 'Электроэнергетика', 'MRKS': 'Электроэнергетика',
    'MRKU': 'Электроэнергетика', 'MRKV': 'Электроэнергетика',
    'MRKY': 'Электроэнергетика', 'MRKZ': 'Электроэнергетика',
    'MSRS': 'Электроэнергетика', 'DVEC': 'Электроэнергетика',
    'LSNG': 'Электроэнергетика', 'VRSB': 'Электроэнергетика',
    'KLSB': 'Электроэнергетика', 'EELT': 'Электроэнергетика',

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
    'KMAZ': 'Машиностроение', 'SVAV': 'Машиностроение',
    'NFAZ': 'Машиностроение', 'MSTT': 'Машиностроение',
    'ZILL': 'Машиностроение',

    # Холдинги (2)
    'AFKS': 'Холдинги', 'LIFE': 'Холдинги',

    # Пищевая (3)
    'GCHE': 'Пищевая', 'ABRD': 'Пищевая', 'AQUA': 'Пищевая',

    # Лес и стройматериалы (2)
    'SGZH': 'Лес и стройматериалы', 'PRFN': 'Лес и стройматериалы',

    # Прочее (4)
    'ABIO': 'Прочее', 'GEMA': 'Прочее', 'KROT': 'Прочее', 'ROLO': 'Прочее',
}

# Проверка: нет дубликатов
assert len(SECTORS) == 87, f"Expected 87 tickers, got {len(SECTORS)}"

# ── Загружаем данные ─────────────────────────────────────────────────────
df = pd.read_csv(PANEL_FILE, parse_dates=['begin'])
df['sector'] = df['ticker'].map(SECTORS).fillna('Прочее')
df['log_amihud'] = np.log1p(df['amihud'] * 1e9)

BREAK = pd.Timestamp('2022-02-24')
df['period'] = np.where(df['begin'] < BREAK, 'pre', 'post')

# ── 1. Средняя доходность по компаниям ──────────────────────────────────
company_stats = df.groupby(['ticker', 'period'])['ret'].mean().unstack()
company_stats.columns = ['post_ret', 'pre_ret']
company_stats['change'] = company_stats['post_ret'] - company_stats['pre_ret']
company_stats['sector'] = company_stats.index.map(SECTORS).fillna('Прочее')

# Добавляем средние факторы (с log_amihud)
fund_means = df.groupby('ticker')[['size', 'leverage', 'bm', 'amihud', 'log_amihud']].mean()
company_stats = company_stats.join(fund_means)

# ── 2. Winners и Losers ─────────────────────────────────────────────────
print("="*70)
print("WINNERS: ТОП-20% по доходности в POST-PERIOD")
print("="*70)
threshold_top = company_stats['post_ret'].quantile(0.80)
winners = company_stats[company_stats['post_ret'] >= threshold_top].sort_values('post_ret', ascending=False)
print(f"\n{'Тикер':<8} {'Сектор':<22} {'Pre ret':>8} {'Post ret':>8} "
      f"{'Size':>6} {'Lev':>6} {'B/M':>6} {'LogAmih':>8}")
print("-"*75)
for ticker, row in winners.iterrows():
    print(f"{ticker:<8} {row['sector']:<22} {row['pre_ret']:>8.4f} "
          f"{row['post_ret']:>8.4f} {row['size']:>6.1f} "
          f"{row['leverage']:>6.2f} {row['bm']:>6.2f} "
          f"{row['log_amihud']:>8.2f}")

print("\n" + "="*70)
print("LOSERS: НИЖНИЕ 20% по доходности в POST-PERIOD")
print("="*70)
threshold_bot = company_stats['post_ret'].quantile(0.20)
losers = company_stats[company_stats['post_ret'] <= threshold_bot].sort_values('post_ret')
print(f"\n{'Тикер':<8} {'Сектор':<22} {'Pre ret':>8} {'Post ret':>8} "
      f"{'Size':>6} {'Lev':>6} {'B/M':>6} {'LogAmih':>8}")
print("-"*75)
for ticker, row in losers.iterrows():
    print(f"{ticker:<8} {row['sector']:<22} {row['pre_ret']:>8.4f} "
          f"{row['post_ret']:>8.4f} {row['size']:>6.1f} "
          f"{row['leverage']:>6.2f} {row['bm']:>6.2f} "
          f"{row['log_amihud']:>8.2f}")

# ── 3. Средние характеристики winners vs losers ────────────────────────
print("\n" + "="*70)
print("СРАВНЕНИЕ ХАРАКТЕРИСТИК: Winners vs Losers")
print("="*70)
print(f"\n{'Характеристика':<20} {'Winners':>10} {'Losers':>10} {'Разница':>10}")
print("-"*55)
for col, label in [('size', 'Size (log assets)'), ('leverage', 'Leverage'),
                    ('bm', 'B/M ratio'), ('log_amihud', 'Log Amihud')]:
    w_mean = winners[col].mean()
    l_mean = losers[col].mean()
    print(f"{label:<20} {w_mean:>10.3f} {l_mean:>10.3f} {w_mean-l_mean:>+10.3f}")

# ── 4. Доходность по секторам ───────────────────────────────────────────
print("\n" + "="*70)
print("ДОХОДНОСТЬ ПО СЕКТОРАМ: Pre vs Post 2022")
print("="*70)
sector_stats = company_stats.groupby('sector')[['pre_ret', 'post_ret', 'change']].mean()
sector_stats = sector_stats.sort_values('post_ret', ascending=False)
sector_counts = company_stats.groupby('sector').size().rename('n')
sector_stats = sector_stats.join(sector_counts)

print(f"\n{'Сектор':<22} {'N':>3} {'Pre ret':>8} {'Post ret':>9} {'Изменение':>10}")
print("-"*55)
for sector, row in sector_stats.iterrows():
    arrow = '↑' if row['change'] > 0 else '↓'
    print(f"{sector:<22} {int(row['n']):>3} {row['pre_ret']:>8.4f} "
          f"{row['post_ret']:>9.4f} {row['change']:>+9.4f} {arrow}")

# ── 5. Наиболее улучшившиеся и ухудшившиеся ─────────────────────────────
print("\n" + "="*70)
print("ТОП-10 КОМПАНИЙ ПО УЛУЧШЕНИЮ ДОХОДНОСТИ (post - pre)")
print("="*70)
top_improvers = company_stats.sort_values('change', ascending=False).head(10)
print(f"\n{'Тикер':<8} {'Сектор':<22} {'Pre':>8} {'Post':>8} {'Изменение':>10}")
print("-"*60)
for ticker, row in top_improvers.iterrows():
    print(f"{ticker:<8} {row['sector']:<22} {row['pre_ret']:>8.4f} "
          f"{row['post_ret']:>8.4f} {row['change']:>+10.4f}")

print("\n" + "="*70)
print("ТОП-10 КОМПАНИЙ ПО УХУДШЕНИЮ ДОХОДНОСТИ (post - pre)")
print("="*70)
top_decliners = company_stats.sort_values('change').head(10)
print(f"\n{'Тикер':<8} {'Сектор':<22} {'Pre':>8} {'Post':>8} {'Изменение':>10}")
print("-"*60)
for ticker, row in top_decliners.iterrows():
    print(f"{ticker:<8} {row['sector']:<22} {row['pre_ret']:>8.4f} "
          f"{row['post_ret']:>8.4f} {row['change']:>+10.4f}")

print("\nГотово!")