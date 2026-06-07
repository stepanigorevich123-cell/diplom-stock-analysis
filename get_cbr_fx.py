import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Коды валют ЦБ РФ
CURRENCIES = {
    'USD': 'R01235',
    'EUR': 'R01239',
}

YEARS = range(2018, 2025)  # 2018–2024

def get_daily_rates(currency_code: str, year: int, retries: int = 3) -> list[float]:
    """Запрашивает дневные курсы валюты за год через API ЦБ (рабочие дни)."""
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
            rates = []
            for record in root.findall('Record'):
                value_str = record.find('Value').text.replace(',', '.')
                rates.append(float(value_str))
            return rates
        except Exception as e:
            if attempt < retries - 1:
                print(f"    Попытка {attempt+1} неудачна, повтор через 3 сек...")
                time.sleep(3)
            else:
                raise e


results = {}

for ccy, code in CURRENCIES.items():
    results[ccy] = {}
    for year in YEARS:
        rates = get_daily_rates(code, year)
        avg = sum(rates) / len(rates) if rates else None
        results[ccy][year] = round(avg, 4) if avg else None
        print(f"{ccy} {year}: среднегодовой = {results[ccy][year]:.4f}  ({len(rates)} дней)")

print("\n" + "="*50)
print("Итоговая таблица:")
df = pd.DataFrame(results)
print(df.to_string())

print("\nДля вставки в скрипт 10_parse_cbonds.py:")
for ccy in CURRENCIES:
    vals = {y: results[ccy][y] for y in YEARS}
    print(f"FX_{ccy} = {vals}")