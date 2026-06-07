import pandas as pd

df = pd.read_csv(r"D:\diplom\data\cbonds_msfo.csv")

pd.set_option('display.float_format', '{:,.1f}'.format)

ydex = df[df['ticker'] == 'YDEX'].sort_values('year')
print("YDEX (Яндекс) — все годы, млн руб:")
print(ydex[['year', 'assets', 'revenue', 'equity', 'debt_total']].to_string(index=False))