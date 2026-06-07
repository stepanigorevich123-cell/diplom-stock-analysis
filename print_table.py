import pandas as pd

df = pd.read_csv(r"D:\diplom\data\cbonds_msfo.csv")
df24 = df[df['year'] == 2024][['ticker', 'assets', 'revenue', 'equity', 'debt_total']].sort_values('assets', ascending=False)

pd.set_option('display.max_rows', 200)
pd.set_option('display.float_format', '{:,.1f}'.format)

print(f"Компаний: {len(df24)}")
print()
print(df24.to_string(index=False))