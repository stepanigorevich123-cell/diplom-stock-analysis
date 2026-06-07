import pandas as pd
import numpy as np

fund   = pd.read_csv(r"D:\diplom\data\cbonds_msfo.csv")
prices = pd.read_csv(r"D:\diplom\data\weekly_prices_clean.csv")
mkt    = pd.read_csv(r"D:\diplom\data\market_cap.csv")

# Pre-period: 2019-2021 (фундаментальные данные), Post: 2022-2024
PRE_YEARS  = [2019, 2020, 2021]
POST_YEARS = [2022, 2023, 2024]

results = []

for ticker in sorted(fund['ticker'].unique()):
    sub = fund[fund['ticker'] == ticker]

    # Leverage: debt_total / assets
    sub_pre  = sub[sub['year'].isin(PRE_YEARS)]
    sub_post = sub[sub['year'].isin(POST_YEARS)]

    # Есть ли leverage в pre
    pre_lev = sub_pre['debt_total'].notna().any() and sub_pre['assets'].notna().any()
    # Есть ли leverage в post
    post_lev = sub_post['debt_total'].notna().any() and sub_post['assets'].notna().any()

    # Есть ли assets и equity (для size и b/m)
    has_size = sub['assets'].notna().any()
    has_bm   = sub['equity'].notna().any()

    # Есть ли в ценовых данных
    in_prices = ticker in prices['ticker'].unique()

    # Есть ли в market cap
    in_mkt = ticker in mkt['ticker'].values

    results.append({
        'ticker':    ticker,
        'lev_pre':   pre_lev,
        'lev_post':  post_lev,
        'lev_both':  pre_lev and post_lev,
        'has_size':  has_size,
        'has_bm':    has_bm,
        'in_prices': in_prices,
        'in_mkt':    in_mkt,
    })

df = pd.DataFrame(results)

# Компании у которых всё есть
full = df[
    df['lev_both'] &
    df['has_size'] &
    df['has_bm'] &
    df['in_prices'] &
    df['in_mkt']
]

print(f"Компаний со всеми данными (leverage в обоих периодах): {len(full)}")
print("\nСписок:")
print(sorted(full['ticker'].tolist()))

print(f"\n\nКомпании БЕЗ leverage в обоих периодах:")
no_lev = df[~df['lev_both'] & df['in_prices']]
print(f"Таких: {len(no_lev)}")
for _, row in no_lev.iterrows():
    reason = []
    if not row['lev_pre']:  reason.append('нет pre')
    if not row['lev_post']: reason.append('нет post')
    if not row['in_mkt']:   reason.append('нет в market_cap')
    print(f"  {row['ticker']:8s}: {', '.join(reason)}")