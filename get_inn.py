import requests
import pandas as pd
import time

companies = []
tickers = pd.read_csv("D:/diplom/data/weekly_prices_clean.csv")["ticker"].unique().tolist()

print(f"Ищем ИНН для {len(tickers)} компаний...")

for ticker in tickers:
    try:
        url = f"https://iss.moex.com/iss/securities/{ticker}.json"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        desc = data.get("description", {})
        rows = desc.get("data", [])
        cols = desc.get("columns", [])
        
        info = {row[0]: row[2] for row in rows if row[2]}
        
        companies.append({
            "ticker": ticker,
            "name": info.get("NAME", ""),
            "full_name": info.get("FULLNAME", ""),
            "inn": info.get("INN", ""),
            "ogrn": info.get("OGRN", ""),
            "isin": info.get("ISIN", ""),
        })
        time.sleep(0.1)
    except Exception as e:
        companies.append({"ticker": ticker, "name": "", "inn": "", "ogrn": ""})

df = pd.DataFrame(companies)
df.to_csv("D:/diplom/data/companies_inn.csv", index=False)
print(f"\nГотово!")
print(df[["ticker", "name", "inn", "ogrn"]].to_string(index=False))