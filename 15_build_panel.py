import pandas as pd
import numpy as np

PRICES_FILE  = r"D:\diplom\data\weekly_prices_clean.csv"
FUND_FILE    = r"D:\diplom\data\cbonds_msfo.csv"
MKTCAP_FILE  = r"D:\diplom\data\market_cap.csv"
OUTPUT_FILE  = r"D:\diplom\data\panel_data.csv"

KEEP_TICKERS = ['ABIO', 'ABRD', 'AFKS', 'AFLT', 'AKRN', 'ALRS', 'AMEZ', 'APTK', 'AQUA', 'ASTR', 'BELU', 'BRZL', 'CHMF', 'CHMK', 'DVEC', 'EELT', 'ELFV', 'ENPG', 'EUTR', 'FEES', 'FESH', 'FLOT', 'GAZP', 'GCHE', 'GEMA', 'GMKN', 'GTRK', 'HEAD', 'HNFG', 'HYDR', 'IRAO', 'KAZT', 'KLSB', 'KMAZ', 'KROT', 'KZOS', 'LENT', 'LIFE', 'LKOH', 'LSNG', 'LSRG', 'MAGN', 'MGNT', 'MRKC', 'MRKS', 'MRKU', 'MRKV', 'MRKY', 'MRKZ', 'MSRS', 'MSTT', 'MTLR', 'MTSS', 'MVID', 'NFAZ', 'NKHP', 'NKNC', 'NLMK', 'NMTP', 'NSVZ', 'NVTK', 'PHOR', 'PIKK', 'PLZL', 'POSI', 'PRFN', 'RKKE', 'RNFT', 'ROLO', 'RTKM', 'RUAL', 'SELG', 'SGZH', 'SIBN', 'SMLT', 'SOFL', 'SVAV', 'TATN', 'TGKB', 'TGKN', 'TRMK', 'UGLD', 'UNAC', 'UWGN', 'VKCO', 'VRSB', 'VSMO', 'X5', 'YDEX', 'ZILL']

VALID_TICKERS = ['ABIO', 'ABRD', 'AFKS', 'AFLT', 'AKRN', 'ALRS', 'AMEZ', 'AQUA', 'ASTR', 'BELU', 'BRZL', 'CHMF', 'CHMK', 'DVEC', 'EELT', 'ELFV', 'ENPG', 'EUTR', 'FEES', 'FESH', 'FLOT', 'GAZP', 'GCHE', 'GEMA', 'GMKN', 'GTRK', 'HEAD', 'HNFG', 'HYDR', 'IRAO', 'KAZT', 'KLSB', 'KMAZ', 'KROT', 'KZOS', 'LENT', 'LIFE', 'LKOH', 'LSNG', 'LSRG', 'MAGN', 'MGNT', 'MRKC', 'MRKS', 'MRKU', 'MRKV', 'MRKY', 'MRKZ', 'MSRS', 'MSTT', 'MTSS', 'MVID', 'NFAZ', 'NKHP', 'NKNC', 'NLMK', 'NMTP', 'NSVZ', 'NVTK', 'PHOR', 'PIKK', 'PLZL', 'POSI', 'PRFN', 'RNFT', 'ROLO', 'RTKM', 'RUAL', 'SELG', 'SGZH', 'SIBN', 'SMLT', 'SOFL', 'SVAV', 'TATN', 'TGKB', 'TGKN', 'TRMK', 'UGLD', 'UNAC', 'UWGN', 'VKCO', 'VRSB', 'VSMO', 'X5', 'YDEX', 'ZILL']

# ── 1. Загружаем данные ───────────────────────────────────────────────────
prices = pd.read_csv(PRICES_FILE, parse_dates=['begin'])
prices['begin'] = pd.to_datetime(prices['begin'])

# Фильтруем только 90 компаний
prices = prices[prices['ticker'].isin(VALID_TICKERS)]
print(f"Цены после фильтра: {len(prices)} строк, {prices['ticker'].nunique()} компаний")
prices = prices[prices['ticker'].isin(KEEP_TICKERS)]  # фильтр по 90 компаниям
fund   = pd.read_csv(FUND_FILE)
mkt    = pd.read_csv(MKTCAP_FILE)

print(f"Фундаментал: {len(fund)} строк, {fund['ticker'].nunique()} компаний")

# ── 2. Считаем количество акций ───────────────────────────────────────────
# Берём количество акций: сначала из shares_outstanding, иначе market_cap/close
last_prices = prices.sort_values('begin').groupby('ticker')['close'].last()
mkt_idx     = mkt.drop_duplicates(subset=['ticker']).set_index('ticker')
# Если shares_outstanding задан — используем его, иначе считаем из market_cap
mkt_idx['shares'] = mkt_idx['shares_outstanding']
mask_no_shares = mkt_idx['shares'].isna()
mkt_idx.loc[mask_no_shares, 'shares'] = mkt_idx.loc[mask_no_shares, 'market_cap'] / last_prices
shares_dict = mkt_idx['shares'].dropna().to_dict()
print(f"Количество акций рассчитано для {len(shares_dict)} компаний")
print(f"AMEZ в shares_dict: {'AMEZ' in shares_dict}, значение: {shares_dict.get('AMEZ', 'НЕТ')}")
print(f"APTK в shares_dict: {'APTK' in shares_dict}, значение: {shares_dict.get('APTK', 'НЕТ')}")

# ── 3. Publication lag: год T → недели апрель T+1 — март T+2 ─────────────
def fund_year_for_week(date):
    """Какой год фундаментальных данных использовать для данной недели."""
    if date.month >= 4:
        return date.year - 1
    else:
        return date.year - 2

prices['fund_year'] = prices['begin'].apply(fund_year_for_week)

# ── 4. Мёрдж с фундаментальными данными ──────────────────────────────────
fund_sel = fund[['ticker', 'year', 'assets', 'equity', 'debt_total',
                 'revenue', 'debt_short', 'debt_long']].copy()

panel = prices.merge(
    fund_sel,
    left_on=['ticker', 'fund_year'],
    right_on=['ticker', 'year'],
    how='left'
)

print(f"\nПосле мёрджа: {len(panel)} строк")

# ── 5. Капитализация на каждую неделю ─────────────────────────────────────
panel['shares'] = panel['ticker'].map(shares_dict)
# ══════════════════════════════════════════════════════════════════
# ВСТАВИТЬ в 15_build_panel.py ПОСЛЕ строки:
#   panel['shares'] = panel['ticker'].map(shares_dict)
# и ПЕРЕД строкой:
#   panel['mktcap'] = panel['close'] * panel['shares']
# ══════════════════════════════════════════════════════════════════
 
# ── 5a. Корректировка на сплиты акций ────────────────────────────────────
# Shares рассчитаны из текущего (post-split) market_cap / last_close.
# Для pre-split периода нужно делить shares на коэффициент сплита,
# чтобы mktcap = close * shares давала корректное значение.
#
# BELU (Novabev/Белуга): квази-сплит 1:8, август 2024
#   Торги остановлены 16.08.2024, возобновлены ~23.08.2024 по новой цене.
#   Цены в API НЕ adjusted (до сплита ~4000-5000, после ~500-700).
#   shares_dict содержит post-split кол-во (~115 млн).
#   Для недель до 2024-08-23 делим shares на 8.
 
SPLITS = {
    'BELU': {'date': pd.Timestamp('2024-08-23'), 'ratio': 8},
}
 
for ticker, split in SPLITS.items():
    mask = (panel['ticker'] == ticker) & (panel['begin'] < split['date'])
    n_adjusted = mask.sum()
    if n_adjusted > 0:
        panel.loc[mask, 'shares'] = panel.loc[mask, 'shares'] / split['ratio']
        print(f"SPLIT FIX: {ticker} — shares divided by {split['ratio']} "
              f"for {n_adjusted} rows before {split['date'].date()}")
        
panel['mktcap'] = panel['close'] * panel['shares']  # в рублях

# ── 6. Строим переменные ──────────────────────────────────────────────────

# Size = log(активы в млн руб)
panel['size'] = np.log(panel['assets'])

# Leverage = total debt / assets
panel['leverage'] = panel['debt_total'] / panel['assets']

# B/M = equity (млн руб) / mktcap (руб) → переводим equity в рубли
# equity в млн руб → умножаем на 1,000,000
panel['bm'] = (panel['equity'] * 1_000_000) / panel['mktcap']

# Excess return (относительно нуля — безрисковую ставку добавим позже)
# return уже есть в ценовом файле
panel.rename(columns={'return': 'ret'}, inplace=True)

# ── 7. Чистим ─────────────────────────────────────────────────────────────
# Убираем строки где нет ключевых переменных (без leverage)
before = len(panel)
panel = panel.dropna(subset=['assets', 'equity', 'mktcap', 'ret', 'size', 'bm'])
after = len(panel)
print(f"Строк после удаления NaN в ключевых переменных (без leverage): {after} (убрано {before-after})")

# Ограничиваем период: апрель 2019 — февраль 2026
panel = panel[(panel['begin'] >= pd.Timestamp('2019-04-01')) & (panel['begin'] <= pd.Timestamp('2026-02-28'))]
print(f"Строк после обрезки периода (апр 2019 – фев 2026): {len(panel)}")

# Убираем экстремальные значения B/M (отрицательный капитал или >10)
panel = panel[panel['bm'] > 0]
panel = panel[panel['bm'] < 10]
print(f"Строк после фильтра B/M [0, 10]: {len(panel)}")

# Убираем отрицательный leverage
panel = panel[panel['leverage'].isna() | (panel['leverage'] >= 0)]

# ── 8. Отбираем нужные колонки ────────────────────────────────────────────
keep_cols = [
    'ticker', 'begin', 'fund_year',
    'ret', 'amihud', 'momentum', 'post',
    'close', 'mktcap', 'shares',
    'assets', 'equity', 'debt_total', 'revenue',
    'size', 'leverage', 'bm',
]
panel = panel[keep_cols].copy()
panel = panel.sort_values(['ticker', 'begin']).reset_index(drop=True)

# ── 9. Сохраняем ──────────────────────────────────────────────────────────
panel.to_csv(OUTPUT_FILE, index=False)
print(f"\nСохранено: {OUTPUT_FILE}")
print(f"Итого: {len(panel)} строк, {panel['ticker'].nunique()} компаний")

# Какие компании потерялись
all_tickers  = set(prices['ticker'].unique())
panel_tickers = set(panel['ticker'].unique())
lost = all_tickers - panel_tickers
print(f"\nПотеряно компаний: {len(lost)}")
print(f"Какие: {sorted(lost)}")

# ── 10. Описательная статистика ───────────────────────────────────────────
print("\nОписательная статистика ключевых переменных:")
print(panel[['ret', 'size', 'leverage', 'bm', 'momentum']].describe().round(4))

print("\nКомпаний по годам:")
panel['year_str'] = panel['begin'].dt.year
print(panel.groupby('year_str')['ticker'].nunique())