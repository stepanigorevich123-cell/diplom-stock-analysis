import pandas as pd

mkt = pd.read_csv(r"D:\diplom\data\market_cap.csv")

# Проверяем текущее состояние
print("AMEZ в market_cap:")
print(mkt[mkt['ticker']=='AMEZ'])
print("\nAPTK в market_cap:")
print(mkt[mkt['ticker']=='APTK'])

# Обновляем shares_outstanding напрямую
mkt.loc[mkt['ticker']=='AMEZ', 'shares_outstanding'] = 498_454_822
mkt.loc[mkt['ticker']=='APTK', 'shares_outstanding'] = 7_630_433_826

mkt.to_csv(r"D:\diplom\data\market_cap.csv", index=False)
print("\nПосле обновления:")
print(mkt[mkt['ticker'].isin(['AMEZ','APTK'])])