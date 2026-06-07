import pandas as pd

df = pd.read_csv('D:/diplom/data/weekly_prices_clean.csv')
print('До:', df['ticker'].nunique(), 'акций')

exclude = ['USBN', 'ETLN', 'FIXR', 'OZON', 'LNZL']
df = df[~df['ticker'].isin(exclude)]

df.to_csv('D:/diplom/data/weekly_prices_clean.csv', index=False)
print('После:', df['ticker'].nunique(), 'акций')
print('Строк:', len(df))