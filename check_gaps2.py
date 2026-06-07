import requests
import time

def get_all_candles(ticker, start, end):
    all_data = []
    start_pos = 0
    while True:
        r = requests.get(
            f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}/candles.json',
            params={'from': start, 'till': end, 'interval': 24, 'start': start_pos}
        )
        rows = r.json()['candles']['data']
        if not rows:
            break
        all_data.extend(rows)
        if len(rows) < 500:
            break
        start_pos += len(rows)
        time.sleep(0.2)
    return all_data

def check(ticker, start, end):
    rows = get_all_candles(ticker, start, end)
    if rows:
        print(f"  {ticker} ({start}—{end}): {len(rows)} свечей, {rows[0][6][:10]} — {rows[-1][6][:10]}")
    else:
        print(f"  {ticker} ({start}—{end}): НЕТ ДАННЫХ")

print("=== VKCO ===")
check("MAIL", "2019-01-01", "2021-12-31")
check("VKCO", "2021-12-14", "2026-02-28")

print("\n=== HEAD ===")
check("HHRU", "2019-01-01", "2024-09-30")
check("HEAD", "2024-10-01", "2026-02-28")

print("\n=== X5 ===")
check("FIVE", "2019-01-01", "2024-04-30")
check("X5",   "2025-01-01", "2026-02-28")

print("\n=== FIXR ===")
check("FIXP", "2019-01-01", "2025-01-01")
check("FIXR", "2025-08-01", "2026-02-28")