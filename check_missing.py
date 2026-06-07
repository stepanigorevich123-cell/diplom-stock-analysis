import pandas as pd

df = pd.read_csv(r"D:\diplom\data\cbonds_msfo.csv")

cols = ['assets', 'revenue', 'equity', 'debt_total']

print("Компании с пропусками в ключевых полях:\n")
for ticker in sorted(df['ticker'].unique()):
    sub = df[df['ticker'] == ticker].sort_values('year')
    for col in cols:
        missing = sub[sub[col].isna()]['year'].tolist()
        if missing:
            print(f"  {ticker} | {col}: нет данных за {missing}")