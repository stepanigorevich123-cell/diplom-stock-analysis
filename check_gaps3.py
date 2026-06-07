import requests
import time

def get_all(ticker, start, end):
    all_data = []
    pos = 0
    while True:
        r = requests.get(
            f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}/candles.json',
            params={'from': start, 'till': end, 'interval': 24, 'start': pos}
        )
        rows = r.json()['candles']['data']
        if not rows: break
        all_data.extend(rows)
        if len(rows) < 500: break
        pos += len(rows)
        time.sleep(0.2)
    return all_data

# HEAD в сентябре 2024
rows = get_all("HHRU", "2024-08-01", "2024-10-31")
print(f"HHRU авг-окт 2024: {len(rows)} свечей")
if rows: print(f"  {rows[0][6][:10]} — {rows[-1][6][:10]}")

rows = get_all("HEAD", "2024-08-01", "2024-10-31")
print(f"HEAD авг-окт 2024: {len(rows)} свечей")
if rows: print(f"  {rows[0][6][:10]} — {rows[-1][6][:10]}")

# FIXR в 2025
rows = get_all("FIXP", "2025-01-01", "2025-08-31")
print(f"FIXP янв-авг 2025: {len(rows)} свечей")
if rows: print(f"  {rows[0][6][:10]} — {rows[-1][6][:10]}")

rows = get_all("FIXR", "2025-01-01", "2025-08-31")
print(f"FIXR янв-авг 2025: {len(rows)} свечей")
if rows: print(f"  {rows[0][6][:10]} — {rows[-1][6][:10]}")