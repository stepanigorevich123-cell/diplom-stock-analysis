import requests
import pandas as pd
import time

# ============================================================
# Скачиваем старые тикеры редомицилированных компаний
# и склеиваем с новыми тикерами
#
# Пары:
# MAIL (2020-2021) + VKCO (2023-2026) → VKCO
# HHRU (2020-2022) + HEAD (2024-2026) → HEAD
# FIVE (2019-2024) + X5  (2024-2026) → X5
# FIXP (2021-2024) + FIXR (2024-2026) → FIXR (если есть)
# ============================================================

def get_daily_prices(ticker, start_date, end_date):
    """Скачивает дневные свечи с пагинацией"""
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
            print(f"  Ошибка {ticker}: {e}")
            break

        candles = data["candles"]
        columns = candles["columns"]
        rows = candles["data"]

        if not rows:
            break

        all_data.extend(rows)

        if len(rows) < 500:
            break

        start += len(rows)
        time.sleep(0.2)

    if not all_data:
        return None

    df = pd.DataFrame(all_data, columns=columns)
    df["begin"] = pd.to_datetime(df["begin"])
    return df


def resample_weekly(df, ticker):
    """Ресемплирует дневные данные в недельные"""
    df = df.set_index("begin")
    weekly = df.resample("W-FRI").agg({
        "open": "first",
        "close": "last",
        "high": "max",
        "low": "min",
        "volume": "sum",
        "value": "sum",
    }).dropna(subset=["close"])
    weekly["ticker"] = ticker
    return weekly.reset_index()


def merge_and_add(old_ticker, old_start, old_end,
                  new_ticker, new_start, new_end,
                  final_ticker):
    """Скачивает старый и новый тикер, склеивает и возвращает недельные данные"""
    print(f"\n{'='*50}")
    print(f"Обрабатываем: {old_ticker} + {new_ticker} → {final_ticker}")

    # Старый тикер
    print(f"  Скачиваем {old_ticker} ({old_start} — {old_end})...")
    old_df = get_daily_prices(old_ticker, old_start, old_end)
    if old_df is not None:
        print(f"  {old_ticker}: {len(old_df)} дневных свечей, "
              f"{old_df['begin'].min().date()} — {old_df['begin'].max().date()}")
    else:
        print(f"  {old_ticker}: нет данных")

    # Новый тикер
    print(f"  Скачиваем {new_ticker} ({new_start} — {new_end})...")
    new_df = get_daily_prices(new_ticker, new_start, new_end)
    if new_df is not None:
        print(f"  {new_ticker}: {len(new_df)} дневных свечей, "
              f"{new_df['begin'].min().date()} — {new_df['begin'].max().date()}")
    else:
        print(f"  {new_ticker}: нет данных")

    # Склеиваем
    parts = []
    if old_df is not None:
        old_df["ticker"] = final_ticker
        parts.append(old_df)
    if new_df is not None:
        new_df["ticker"] = final_ticker
        parts.append(new_df)

    if not parts:
        print(f"  Нет данных для {final_ticker}!")
        return None

    combined = pd.concat(parts, ignore_index=True)
    combined = combined.sort_values("begin").drop_duplicates(subset=["begin"])

    print(f"  Итого: {len(combined)} дневных свечей, "
          f"{combined['begin'].min().date()} — {combined['begin'].max().date()}")

    # Недельные данные
    weekly = resample_weekly(combined, final_ticker)
    print(f"  Недельных: {len(weekly)}")
    return weekly


# ============================================================
# Загружаем основной файл цен
# ============================================================

print("Загружаем основной файл...")
prices = pd.read_csv("D:/diplom/data/weekly_prices.csv")
prices["begin"] = pd.to_datetime(prices["begin"])
print(f"Исходно: {prices['ticker'].nunique()} акций")

# ============================================================
# 1. ВК: MAIL (2020-2021) + VKCO (2023-2026)
# Разрыв в 2022 — биржа была закрыта для VK
# ============================================================

vk = merge_and_add(
    old_ticker="MAIL", old_start="2019-01-01", old_end="2021-12-13",
    new_ticker="VKCO", new_start="2021-12-14", new_end="2026-02-28",
    final_ticker="VKCO"
)

# ============================================================
# 2. Хэдхантер: HHRU (2020-2022) + HEAD (2024-2026)
# ============================================================

hh = merge_and_add(
    old_ticker="HHRU", old_start="2019-01-01", old_end="2024-08-09",
    new_ticker="HEAD", new_start="2024-09-26", new_end="2026-02-28",
    final_ticker="HEAD"
)

# ============================================================
# 3. X5: FIVE (2019-2024) + X5 (2024-2026)
# ============================================================

x5 = merge_and_add(
    old_ticker="FIVE", old_start="2019-01-01", old_end="2024-04-30",
    new_ticker="X5",   new_start="2024-07-01", new_end="2026-02-28",
    final_ticker="X5"
)

# ============================================================
# 4. Фикс Прайс: FIXP (2021-2024) + FIXR (2025-2026)
# ============================================================

fixp = merge_and_add(
    old_ticker="FIXP", old_start="2019-01-01", old_end="2025-06-20",
    new_ticker="FIXR", new_start="2025-08-20", new_end="2026-02-28",
    final_ticker="FIXR"
)
# ============================================================
# Обновляем основной файл
# ============================================================

print(f"\n{'='*50}")
print("Обновляем основной файл...")

# Удаляем старые версии этих тикеров
remove_tickers = ["VKCO", "HEAD", "X5", "FIXR", "MAIL", "HHRU", "FIVE", "FIXP"]
prices = prices[~prices["ticker"].isin(remove_tickers)]

# Добавляем новые склеенные серии
new_series = []
for df in [vk, hh, x5, fixp]:
    if df is not None:
        new_series.append(df)

if new_series:
    prices = pd.concat([prices] + new_series, ignore_index=True)
    prices = prices.sort_values(["ticker", "begin"])

print(f"Итого акций: {prices['ticker'].nunique()}")

# Проверяем каждую добавленную компанию
for t in ["VKCO", "HEAD", "X5", "FIXR"]:
    subset = prices[prices["ticker"] == t]
    if len(subset) > 0:
        print(f"{t}: {len(subset)} недель, "
              f"{subset['begin'].min().date()} — {subset['begin'].max().date()}")
    else:
        print(f"{t}: нет в данных")

# Сохраняем
prices.to_csv("D:/diplom/data/weekly_prices.csv", index=False)
print("\nФайл сохранён: data/weekly_prices.csv")
print("Теперь запусти 03_clean_data.py и 06_momentum_v2.py заново!")