import pandas as pd

mkt = pd.read_csv(r"D:\diplom\data\market_cap.csv")
prices = pd.read_csv(r"D:\diplom\data\weekly_prices_clean.csv")

# Берём последнюю дату цен
last_date = prices['begin'].max()
print(f"Последняя дата в ценовых данных: {last_date}")

# Цена на последнюю дату для каждого тикера
last_prices = prices[prices['begin'] == last_date][['ticker', 'close']].set_index('ticker')

# Считаем количество акций = market_cap / close
mkt = mkt.set_index('ticker')
mkt['close_last'] = last_prices['close']
mkt['shares_calc'] = mkt['market_cap'] / mkt['close_last']

print("\nПример расчёта акций:")
print(mkt[['market_cap', 'close_last', 'shares_calc']].dropna().head(10).to_string())
print(f"\nВсего компаний с рассчитанными акциями: {mkt['shares_calc'].notna().sum()}")