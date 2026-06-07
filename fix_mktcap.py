import pandas as pd

mkt = pd.read_csv(r"D:\diplom\data\market_cap.csv")
print("До:", len(mkt), "строк")
print("Дубликаты:", mkt[mkt['ticker'].duplicated()]['ticker'].tolist())

# Убираем дубликаты
mkt = mkt.drop_duplicates(subset=['ticker'], keep='first')

# Добавляем если ещё нет
for ticker, mktcap, shares in [
    ('AMEZ', 33_919_850_637, 498_454_822),
    ('APTK', 65_851_000_000, 7_630_433_826),
]:
    if ticker not in mkt['ticker'].values:
        mkt = pd.concat([mkt, pd.DataFrame([{
            'ticker': ticker,
            'market_cap': mktcap,
            'shares_outstanding': shares
        }])], ignore_index=True)
        print(f"Добавлен {ticker}")
    else:
        print(f"{ticker} уже есть")

mkt.to_csv(r"D:\diplom\data\market_cap.csv", index=False)
print("После:", len(mkt), "строк")
print(mkt[mkt['ticker'].isin(['AMEZ', 'APTK'])])