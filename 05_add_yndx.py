import requests
import pandas as pd
import time

# ============================================================
# Скачиваем YNDX (старый тикер Яндекса до редомициляции)
# и склеиваем с YDEX (новый тикер после редомициляции)
# ============================================================

def get_daily_prices(ticker, start_date, end_date):
    """Скачивает дневные свечи для тикера"""
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
            "interval": 24,
            "start": start,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
        except Exception as e:
            print(f"Ошибка: {e}")
            break

        candles = data["candles"]
        columns = candles["columns"]
        rows = candles["data"]

        if not rows:
            break

        all_data.extend(rows)
        print(f"  {ticker}: скачано {len(all_data)} свечей...")

        if len(rows) < 500:
            break

        start += len(rows)
        time.sleep(0.2)

    if not all_data:
        return None

    df = pd.DataFrame(all_data, columns=columns)
    df["begin"] = pd.to_datetime(df["begin"])
    return df


# ============================================================
# ШАГ 1: Скачиваем YNDX (2019 — март 2022, до заморозки)
# ============================================================

print("Скачиваем YNDX (2019–2022)...")
yndx = get_daily_prices("YNDX", "2019-01-01", "2024-06-14")
if yndx is not None:
    print(f"YNDX: {len(yndx)} дневных свечей")
    print(f"Период: {yndx['begin'].min().date()} — {yndx['begin'].max().date()}")
else:
    print("YNDX не скачался!")
    exit()

# ============================================================
# ШАГ 2: Скачиваем YDEX (июль 2024 — февраль 2026)
# ============================================================

print("\nСкачиваем YDEX (2024–2026)...")
ydex = get_daily_prices("YDEX", "2024-07-01", "2026-02-28")

if ydex is not None:
    print(f"YDEX: {len(ydex)} дневных свечей")
    print(f"Период: {ydex['begin'].min().date()} — {ydex['begin'].max().date()}")
else:
    print("YDEX не скачался!")
    exit()

# ============================================================
# ШАГ 3: Склеиваем в одну серию под тикером YDEX
# Период 2022–2024 пропускаем (акция была заморожена)
# ============================================================

yndx["ticker"] = "YDEX"  # переименовываем в единый тикер
ydex["ticker"] = "YDEX"

combined = pd.concat([yndx, ydex], ignore_index=True)
combined = combined.sort_values("begin").drop_duplicates(subset=["begin"])

print(f"\nОбъединённая серия YDEX: {len(combined)} дневных свечей")
print(f"Период: {combined['begin'].min().date()} — {combined['begin'].max().date()}")

# ============================================================
# ШАГ 4: Ресемплируем в недельные данные
# ============================================================

combined = combined.set_index("begin")
weekly = combined.resample("W-FRI").agg({
    "open": "first",
    "close": "last",
    "high": "max",
    "low": "min",
    "volume": "sum",
    "value": "sum",
}).dropna(subset=["close"])

weekly["ticker"] = "YDEX"
weekly = weekly.reset_index()

print(f"Недельных наблюдений: {len(weekly)}")

# ============================================================
# ШАГ 5: Добавляем в основной файл цен
# ============================================================

prices = pd.read_csv("D:/diplom/data/weekly_prices.csv")
prices["begin"] = pd.to_datetime(prices["begin"])

# Убираем старый YDEX из основного файла
prices = prices[prices["ticker"] != "YDEX"]

# Добавляем новый склеенный YDEX
prices = pd.concat([prices, weekly], ignore_index=True)
prices = prices.sort_values(["ticker", "begin"])

print(f"\nОбновлённый файл: {prices['ticker'].nunique()} акций")
ydex_check = prices[prices["ticker"] == "YDEX"]
print(f"YDEX недель: {len(ydex_check)}")
print(f"YDEX период: {ydex_check['begin'].min().date()} — {ydex_check['begin'].max().date()}")

# Сохраняем
prices.to_csv("D:/diplom/data/weekly_prices.csv", index=False)
print("\nФайл обновлён: data/weekly_prices.csv")
print("Теперь запусти заново 03_clean_data.py чтобы пересобрать чистый файл")