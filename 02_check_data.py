import pandas as pd

df = pd.read_csv("D:/diplom/data/weekly_prices.csv")

print("=== ОБЩАЯ ИНФОРМАЦИЯ ===")
print(f"Строк: {len(df)}")
print(f"Акций: {df['ticker'].nunique()}")
print(f"Период: {df['begin'].min()} — {df['begin'].max()}")

print("\n=== ПЕРВЫЕ 5 СТРОК ===")
print(df.head())

print("\n=== КОЛОНКИ ===")
print(df.columns.tolist())

print("\n=== СКОЛЬКО НЕДЕЛЬ НА АКЦИЮ (топ-10 и боттом-10) ===")
counts = df.groupby('ticker')['begin'].count().sort_values()
print("Меньше всего данных:")
print(counts.head(10))
print("\nБольше всего данных:")
print(counts.tail(10))