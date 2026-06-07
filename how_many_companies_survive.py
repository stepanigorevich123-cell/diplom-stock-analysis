import pandas as pd

df = pd.read_csv(r"D:\diplom\data\cbonds_msfo.csv")

key = ['assets', 'equity', 'revenue']

result = (df.groupby('ticker')
            .apply(lambda x: (x[key].notna().all(axis=1) & x['year'].between(2018, 2024)).sum())
            .reset_index())
result.columns = ['ticker', 'n_complete_years']
result = result.sort_values('n_complete_years')

print(result.to_string(index=False))
print(f"\nКомпаний с полными 7 годами:  {(result['n_complete_years'] == 7).sum()}")
print(f"Компаний с 6+ годами:          {(result['n_complete_years'] >= 6).sum()}")
print(f"Компаний с 5+ годами:          {(result['n_complete_years'] >= 5).sum()}")
print(f"\nКомпаний с < 5 лет данных:")
print(result[result['n_complete_years'] < 5].to_string(index=False))