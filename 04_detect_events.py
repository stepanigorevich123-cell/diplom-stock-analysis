import pandas as pd
import numpy as np

# ============================================================
# ДЕТЕКТОР АНОМАЛЬНЫХ СОБЫТИЙ
# Ищем недели когда акция двигается на ±15%+
# при этом рынок в целом не объясняет это движение
# Такие недели = скорее всего корпоративное событие
# ============================================================

# Загружаем чистые данные
df = pd.read_csv("D:/diplom/data/weekly_prices_clean.csv")
df["begin"] = pd.to_datetime(df["begin"])

print(f"Загружено: {df['ticker'].nunique()} акций, {len(df)} строк")

# ============================================================
# ШАГ 1: Считаем рыночную доходность
# Рыночная доходность = средняя доходность всех акций за неделю
# Это прокси для индекса MOEX
# Если рынок упал на 5% — то и акция упасть на 5% это нормально
# Нас интересует движение СВЕРХ рынка
# ============================================================

market_return = df.groupby("begin")["return"].median().reset_index()
market_return.columns = ["begin", "market_return"]

df = df.merge(market_return, on="begin", how="left")

# Аномальная доходность = доходность акции минус доходность рынка
# Например: акция +20%, рынок +2% → аномальная доходность = +18%
# Это явно корпоративное событие, не рыночное движение
df["abnormal_return"] = df["return"] - df["market_return"]

# ============================================================
# ШАГ 2: Находим аномальные недели
# Порог: аномальная доходность > 15% или < -15%
# ============================================================

threshold = 0.15  # 15%

events = df[df["abnormal_return"].abs() > threshold].copy()
events = events.sort_values("abnormal_return", ascending=False)

print(f"\nНайдено аномальных недель: {len(events)}")
print(f"Уникальных компаний с событиями: {events['ticker'].nunique()}")

# ============================================================
# ШАГ 3: Топ событий — самые резкие движения
# ============================================================

print("\n=== ТОП-30 САМЫХ РЕЗКИХ ДВИЖЕНИЙ ВВЕРХ ===")
top_up = events.nlargest(30, "abnormal_return")[
    ["ticker", "begin", "return", "market_return", "abnormal_return", "volume"]
]
top_up["return"] = (top_up["return"] * 100).round(1).astype(str) + "%"
top_up["market_return"] = (top_up["market_return"] * 100).round(1).astype(str) + "%"
top_up["abnormal_return"] = (top_up["abnormal_return"] * 100).round(1).astype(str) + "%"
print(top_up.to_string(index=False))

print("\n=== ТОП-30 САМЫХ РЕЗКИХ ПАДЕНИЙ ===")
top_down = events.nsmallest(30, "abnormal_return")[
    ["ticker", "begin", "return", "market_return", "abnormal_return", "volume"]
]
top_down["return"] = (top_down["return"] * 100).round(1).astype(str) + "%"
top_down["market_return"] = (top_down["market_return"] * 100).round(1).astype(str) + "%"
top_down["abnormal_return"] = (top_down["abnormal_return"] * 100).round(1).astype(str) + "%"
print(top_down.to_string(index=False))

# ============================================================
# ШАГ 4: Сколько аномальных событий у каждой компании
# Компании с очень частыми событиями — подозрительные
# ============================================================

print("\n=== КОМПАНИИ С НАИБОЛЬШИМ ЧИСЛОМ АНОМАЛЬНЫХ НЕДЕЛЬ ===")
event_counts = events.groupby("ticker").size().sort_values(ascending=False)
print(event_counts.head(20))

# ============================================================
# ШАГ 5: Сохраняем полный список событий для ручной проверки
# ============================================================

events_raw = df[df["abnormal_return"].abs() > threshold].copy()
events_raw["abnormal_return_pct"] = (events_raw["abnormal_return"] * 100).round(2)
events_raw["return_pct"] = (events_raw["return"] * 100).round(2)
events_raw = events_raw[["ticker", "begin", "return_pct", "abnormal_return_pct", "volume", "value"]]
events_raw = events_raw.sort_values(["ticker", "begin"])
events_raw.to_csv("D:/diplom/data/anomalous_events.csv", index=False)

print(f"\nПолный список событий сохранён: data/anomalous_events.csv")
print("Открой его в Excel и посмотри какие события стоят за резкими движениями")

# ============================================================
# ШАГ 6: Список компаний с редомициляцией
# Добавляем dummy вручную — это известные факты
# ============================================================

relocation_events = {
    "YDEX": "2024-07-01",   # Яндекс — переезд из Нидерландов
    "HEAD": "2024-09-01",   # Хэдхантер — переезд с Кипра
    "VKCO": "2023-07-01",   # ВК — переезд с БВО
    "GEMC": "2023-10-01",   # ЮМГ — переезд с Кипра
    "OZON": "2024-01-01",   # Озон — реструктуризация
    "FLOT": "2022-06-01",   # Совкомфлот
    "RAGR": "2024-06-01",   # Русагро
}

print("\n=== КОМПАНИИ С РЕДОМИЦИЛЯЦИЕЙ ===")
for ticker, date in relocation_events.items():
    if ticker in df["ticker"].unique():
        print(f"{ticker}: редомициляция ~{date}")
    else:
        print(f"{ticker}: нет в выборке")

# Добавляем relocation dummy в чистые данные
df["relocation"] = 0
for ticker, date in relocation_events.items():
    mask = (df["ticker"] == ticker) & (df["begin"] >= date)
    df.loc[mask, "relocation"] = 1

relocation_count = df["relocation"].sum()
print(f"\nСтрок помечено как релокация: {relocation_count}")

# Сохраняем обновлённые данные с relocation dummy
df.to_csv("D:/diplom/data/weekly_prices_clean.csv", index=False)
print("Данные обновлены с relocation dummy")