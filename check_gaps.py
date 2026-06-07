import requests

def check_ticker(ticker, start, end):
    r = requests.get(
        f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}/candles.json',
        params={'from': start, 'till': end, 'interval': 24}
    )
    rows = r.json()['candles']['data']
    if rows:
        print(f"  {ticker} ({start}—{end}): {len(rows)} свечей, {rows[0][6][:10]} — {rows[-1][6][:10]}")
    else:
        print(f"  {ticker} ({start}—{end}): НЕТ ДАННЫХ")

print("=== VKCO ===")
check_ticker("MAIL", "2019-01-01", "2021-12-31")
check_ticker("VKCO", "2022-01-01", "2022-12-31")
check_ticker("VKCO", "2023-01-01", "2026-02-28")

print("\n=== HEAD ===")
check_ticker("HHRU", "2019-01-01", "2024-09-30")
check_ticker("HEAD", "2024-10-01", "2026-02-28")

print("\n=== X5 ===")
check_ticker("FIVE", "2019-01-01", "2024-04-30")
check_ticker("X5",   "2024-04-01", "2024-12-31")
check_ticker("X5",   "2025-01-01", "2026-02-28")

print("\n=== FIXR ===")
check_ticker("FIXP", "2019-01-01", "2025-01-01")
check_ticker("FIXR", "2024-01-01", "2025-08-01")
check_ticker("FIXR", "2025-08-01", "2026-02-28")