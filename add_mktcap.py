import pandas as pd

mkt = pd.read_csv(r"D:\diplom\data\market_cap.csv")
print("До:", len(mkt), "компаний")

# Добавляем AMEZ и APTK
new_rows = pd.DataFrame([
    {'ticker': 'AMEZ', 'market_cap': 33_919_850_637, 'shares_outstanding': 498_454_822},
    {'ticker': 'APTK', 'market_cap': 65_851_000_000, 'shares_outstanding': 7_630_433_826},
])

mkt = pd.concat([mkt, new_rows], ignore_index=True)
mkt.to_csv(r"D:\diplom\data\market_cap.csv", index=False)
print("После:", len(mkt), "компаний")
print(mkt[mkt['ticker'].isin(['AMEZ', 'APTK'])])