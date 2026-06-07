import pandas as pd
import numpy as np

fund = pd.read_csv(r"D:\diplom\data\cbonds_msfo.csv")
mkt  = pd.read_csv(r"D:\diplom\data\market_cap.csv")
prices = pd.read_csv(r"D:\diplom\data\weekly_prices_clean.csv", parse_dates=['begin'])

last_date   = prices['begin'].max()
last_prices = prices[prices['begin'] == last_date][['ticker','close']].set_index('ticker')
mkt_idx     = mkt.drop_duplicates('ticker').set_index('ticker')
mkt_idx['shares'] = mkt_idx['market_cap'] / last_prices['close']

for ticker in ['AMEZ', 'APTK']:
    print(f"\n=== {ticker} ===")
    f = fund[fund['ticker']==ticker][['year','assets','equity','debt_total']]
    print(f.to_string(index=False))
    
    if ticker in mkt_idx.index:
        shares = mkt_idx.loc[ticker, 'shares']
        print(f"shares: {shares:,.0f}")
        
        # Проверяем B/M
        p = prices[(prices['ticker']==ticker)].tail(5)
        p['mktcap'] = p['close'] * shares
        p['bm_check'] = None
        for _, row in f.iterrows():
            eq = row['equity']
            print(f"  {row['year']}: equity={eq:,.1f} → {'OK' if eq > 0 else 'NEGATIVE!'}")
    else:
        print(f"НЕТ В MARKET_CAP!")