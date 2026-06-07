import pandas as pd

df = pd.read_csv(r'D:\diplom\data\cbonds_msfo.csv')

# Берём 2024 год как самый свежий
df24 = df[df['year'] == 2024][['ticker', 'assets', 'revenue', 'equity', 'debt_total']].copy()
df24 = df24.sort_values('assets', ascending=False)

print(df24.to_string(index=False))