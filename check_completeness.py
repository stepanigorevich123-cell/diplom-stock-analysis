import pandas as pd

df = pd.read_csv(r"D:\diplom\data\panel_data.csv")

key_vars = ['ret', 'size', 'leverage', 'bm', 'momentum']

# Компании у которых ВСЕ ключевые переменные есть хотя бы в 80% наблюдений
completeness = df.groupby('ticker').apply(
    lambda x: (x[key_vars].notna().all(axis=1)).mean()
).reset_index()
completeness.columns = ['ticker', 'complete_pct']
completeness = completeness.sort_values('complete_pct', ascending=False)

print("Распределение полноты данных:")
print(f"  >95% полных наблюдений: {(completeness['complete_pct'] >= 0.95).sum()} компаний")
print(f"  >90% полных наблюдений: {(completeness['complete_pct'] >= 0.90).sum()} компаний")
print(f"  >80% полных наблюдений: {(completeness['complete_pct'] >= 0.80).sum()} компаний")
print(f"  >50% полных наблюдений: {(completeness['complete_pct'] >= 0.50).sum()} компаний")

print("\nКомпании с <80% полных наблюдений:")
bad = completeness[completeness['complete_pct'] < 0.80]
print(bad.to_string(index=False))