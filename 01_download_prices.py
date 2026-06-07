import requests
import pandas as pd
import time
from tqdm import tqdm
 
# ============================================================
# ШАГ 1: Получаем список всех акций с МосБиржи
# ============================================================
 
def get_all_stocks():
    """Скачивает список всех акций с основного режима TQBR"""
    url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json"
    params = {"start": 0}
 
    response = requests.get(url, params=params)
    data = response.json()
 
    securities = data["securities"]
    columns = securities["columns"]
    rows = securities["data"]
 
    df = pd.DataFrame(rows, columns=columns)
    df = df[["SECID", "SHORTNAME", "LOTSIZE", "ISIN"]].copy()
    print(f"Найдено акций на TQBR: {len(df)}")
    return df
 
 
# ============================================================
# ШАГ 2: Скачиваем дневные цены для одной акции
# ============================================================
 
def get_weekly_prices(ticker, start_date="2019-01-01", end_date="2026-02-28"):
    """
    Скачивает дневные свечи с МосБиржи и ресемплирует в недельные.
    ticker: например 'SBER', 'LKOH'
    """
    all_data = []
    start = 0
 
    while True:
        url = (
            f"https://iss.moex.com/iss/engines/stock/markets/shares/"
            f"boards/TQBR/securities/{ticker}/candles.json"
        )
        params = {
            "from": start_date,
            "till": end_date,
            "interval": 24,  # дневные свечи
            "start": start,
        }
 
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
        except Exception:
            break
 
        candles = data["candles"]
        columns = candles["columns"]
        rows = candles["data"]
 
        if not rows:
            break
 
        all_data.extend(rows)
 
        if len(rows) < 500:  # меньше максимума = конец данных
            break
 
        start += len(rows)
        time.sleep(0.2)  # пауза чтобы не перегружать API
 
    if not all_data:
        return None
 
    df = pd.DataFrame(all_data, columns=columns)
    df["begin"] = pd.to_datetime(df["begin"])
    df = df.set_index("begin")
 
    # Ресемплируем в недельные данные (конец недели = пятница)
    weekly = df.resample("W-FRI").agg(
        {
            "open": "first",
            "close": "last",
            "high": "max",
            "low": "min",
            "volume": "sum",
            "value": "sum",  # оборот в рублях — нужен для расчёта Amihud
        }
    ).dropna(subset=["close"])
 
    weekly["ticker"] = ticker
    return weekly
 
 
# ============================================================
# ШАГ 3: Скачиваем все акции и сохраняем
# ============================================================
 
if __name__ == "__main__":
    # Получаем список акций
    print("Получаем список акций...")
    stocks = get_all_stocks()
    stocks.to_csv("D:/diplom/data/stocks_list.csv", index=False)
    print(f"Список сохранён: data/stocks_list.csv")
 
    tickers = stocks["SECID"].tolist()
 
    # Скачиваем цены по каждой акции
    all_prices = []
    failed = []
 
    print(f"\nСкачиваем цены для {len(tickers)} акций...")
 
    for ticker in tqdm(tickers):
        try:
            df = get_weekly_prices(ticker)
            if df is not None and len(df) > 50:  # минимум 50 недель данных
                all_prices.append(df.reset_index())
        except Exception as e:
            failed.append(ticker)
            continue
 
    # Объединяем всё в один датафрейм
    print("\nОбъединяем данные...")
    prices = pd.concat(all_prices, ignore_index=True)
 
    # Сохраняем
    prices.to_csv("D:/diplom/data/weekly_prices.csv", index=False)
    print(f"\nГотово! Сохранено {len(prices)} строк по {prices['ticker'].nunique()} акциям")
    print(f"Файл: data/weekly_prices.csv")
 
    if failed:
        print(f"Не удалось скачать ({len(failed)} тикеров): {failed}")