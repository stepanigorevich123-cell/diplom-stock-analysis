import pandas as pd

df = pd.read_csv(r"D:\diplom\data\cbonds_msfo.csv")

# Проверяем несколько компаний у которых debt_total пуст
for ticker in ['UPRO', 'SNGS', 'RASP', 'PMSB', 'TTLK']:
    print(f"\n{ticker}:")
    print(df[df['ticker']==ticker][['year','debt_short','debt_long','debt_total']].to_string(index=False))