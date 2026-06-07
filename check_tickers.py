import requests

tickers = ['HHRU', 'FIVE', 'FIXP', 'TCSG', 'MAIL']
for t in tickers:
    r = requests.get(
        f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{t}/candles.json',
        params={'from': '2019-01-01', 'till': '2025-12-31', 'interval': 24}
    )
    rows = r.json()['candles']['data']
    if rows:
        print(f'{t}: {rows[0][6][:10]} — {rows[-1][6][:10]}, {len(rows)} свечей')
    else:
        print(f'{t}: нет данных')
        