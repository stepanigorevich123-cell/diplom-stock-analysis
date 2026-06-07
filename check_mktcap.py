import pandas as pd

df = pd.read_csv(r"D:\diplom\data\market_cap.csv")
print("Колонки:", df.columns.tolist())
print("Строк:", len(df))
print("\nПервые строки:")
print(df.head(5))
print("\nГАЗП:")
print(df[df['ticker']=='GAZP'].head(5))