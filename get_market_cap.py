import requests
import pandas as pd
import time

tickers = pd.read_csv("D:/diplom/data/weekly_prices_clean.csv")["ticker"].unique().tolist()

results = []
for ticker in tickers:
    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
    r = requests.get(url, timeout=10)
    data = r.json()
    
    rows = data.get("marketdata", {}).get("data", [])
    cols = data.get("marketdata", {}).get("columns", [])
    
    if rows:
        row = dict(zip(cols, rows[0]))
        results.append({
            "ticker": ticker,
            "market_cap": row.get("ISSUECAPITALIZATION"),
            "shares_outstanding": row.get("ISSUESIZE"),
        })
        print(f"{ticker}: {row.get('ISSUECAPITALIZATION')}")
    
    time.sleep(0.1)

df = pd.DataFrame(results)
df.to_csv("D:/diplom/data/market_cap.csv", index=False)
print("Готово!")
