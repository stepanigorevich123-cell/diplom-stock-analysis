import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_DIR = r"D:\diplom\data"

CURRENCIES = {
    'USD': 'R01235',
    'EUR': 'R01239',
}

YEARS = range(2018, 2025)  # 2018–2024

def get_daily_rates(currency_code: str, year: int, retries: int = 3) -> dict:
    """Возвращает словарь {date_str: rate} за весь год."""
    date_from = f"01/01/{year}"
    date_to   = f"31/12/{year}"
    url = (
        f"https://www.cbr.ru/scripts/XML_dynamic.asp"
        f"?date_req1={date_from}&date_req2={date_to}&VAL_NM_RQ={currency_code}"
    )
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=30, verify=False)
            resp.encoding = 'windows-1251'
            root = ET.fromstring(resp.text)
            result = {}
            for record in root.findall('Record'):
                date_str = record.attrib.get('Date', '')
                value_str = record.find('Value').text.replace(',', '.')
                result[date_str] = float(value_str)
            return result
        except Exception as e:
            if attempt < retries - 1:
                print(f"    Попытка {attempt+1} неудачна, повтор через 3 сек...")
                time.sleep(3)
            else:
                raise e


# ── Собираем данные ────────────────────────────────────────────────────────
avg_rows  = []  # среднегодовые
eoy_rows  = []  # на конец года (31 декабря или последний рабочий день)

for ccy, code in CURRENCIES.items():
    for year in YEARS:
        print(f"Скачиваю {ccy} {year}...")
        rates = get_daily_rates(code, year)

        if not rates:
            print(f"  WARN: нет данных для {ccy} {year}")
            continue

        # Среднегодовой
        avg_rate = sum(rates.values()) / len(rates.values())

        # Курс на конец года — берём последнюю дату в декабре
        dec_rates = {d: r for d, r in rates.items() if d.startswith('31.12') or d.startswith('30.12') or d.startswith('29.12') or d.startswith('28.12')}
        last_date = sorted(dec_rates.keys())[-1] if dec_rates else sorted(rates.keys())[-1]
        eoy_rate = rates[last_date]

        avg_rows.append({'year': year, 'currency': ccy, 'rate_avg': round(avg_rate, 4)})
        eoy_rows.append({'year': year, 'currency': ccy, 'date': last_date, 'rate_eoy': round(eoy_rate, 4)})

        print(f"  среднегодовой: {avg_rate:.4f} | конец года ({last_date}): {eoy_rate:.4f} | дней: {len(rates)}")

# ── Сохраняем ─────────────────────────────────────────────────────────────
df_avg = pd.DataFrame(avg_rows)
df_eoy = pd.DataFrame(eoy_rows)

# Широкий формат (год × валюта)
df_avg_wide = df_avg.pivot(index='year', columns='currency', values='rate_avg').reset_index()
df_avg_wide.columns.name = None

df_eoy_wide = df_eoy.pivot(index='year', columns='currency', values='rate_eoy').reset_index()
df_eoy_wide.columns.name = None

path_avg = rf"{OUTPUT_DIR}\fx_rates_avg.csv"
path_eoy = rf"{OUTPUT_DIR}\fx_rates_eoy.csv"

df_avg_wide.to_csv(path_avg, index=False)
df_eoy_wide.to_csv(path_eoy, index=False)

print(f"\n{'='*50}")
print(f"Сохранено: {path_avg}")
print(df_avg_wide.to_string(index=False))
print(f"\nСохранено: {path_eoy}")
print(df_eoy_wide.to_string(index=False))