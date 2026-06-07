import os
import requests
import pandas as pd
import time

# Ключи DaData читаются из переменных окружения, чтобы не хранить их в коде.
# Перед запуском задайте: export DADATA_API_KEY=... и export DADATA_SECRET_KEY=...
API_KEY = os.environ["DADATA_API_KEY"]
SECRET_KEY = os.environ["DADATA_SECRET_KEY"]

companies = [
    ("ABIO", "Артген"), ("ABRD", "Абрау-Дюрсо"), ("AFKS", "АФК Система"),
    ("AFLT", "Аэрофлот"), ("AKRN", "Акрон"), ("ALRS", "АЛРОСА"),
    ("AMEZ", "Ашинский метзавод"), ("APTK", "Аптечная сеть 36.6"),
    ("AQUA", "ИНАРКТИКА"), ("ASTR", "Группа Астра"), ("BANE", "Башнефть"),
    ("BELU", "НоваБев Групп"), ("BLNG", "Белон"), ("BRZL", "Бурятзолото"),
    ("CARM", "СТГ"), ("CHMF", "Северсталь"), ("CHMK", "ЧМК"),
    ("CNTL", "Центральный Телеграф"), ("DELI", "Каршеринг Руссия"),
    ("DIAS", "Диасофт"), ("DVEC", "ДЭК"), ("EELT", "ЕвропЭлектротехника"),
    ("ELFV", "ЭЛ5-Энерго"), ("ENPG", "ЭН+ ГРУП"), ("ETLN", "Эталон"),
    ("EUTR", "ЕвроТранс"), ("FEES", "ФСК Россети"), ("FESH", "ДВМП"),
    ("FIXR", "Фикс Прайс"), ("FLOT", "Совкомфлот"), ("GAZP", "Газпром"),
    ("GCHE", "Группа Черкизово"), ("GECO", "ГЕНЕТИКО"), ("GEMA", "ММЦБ"),
    ("GEMC", "Юнайтед Медикал"), ("GMKN", "Норильский никель"),
    ("GTRK", "ГТМ"), ("HEAD", "Хэдхантер"), ("HNFG", "ХЭНДЕРСОН"),
    ("HYDR", "РусГидро"), ("IRAO", "Интер РАО"), ("IRKT", "Яковлев"),
    ("KAZT", "Куйбышевазот"), ("KLSB", "Калужская сбытовая"),
    ("KLVZ", "Кристалл"), ("KMAZ", "КАМАЗ"), ("KROT", "Красный Октябрь"),
    ("KZOS", "Органический синтез"), ("LENT", "Лента"), ("LIFE", "Фармсинтез"),
    ("LKOH", "ЛУКОЙЛ"), ("LNZL", "Лензолото"), ("LSNG", "Россети Ленэнерго"),
    ("LSRG", "Группа ЛСР"), ("MAGN", "ММК"), ("MDMG", "МД Медикал"),
    ("MGNT", "Магнит"), ("MRKC", "Россети Центр"), ("MRKS", "Россети Сибирь"),
    ("MRKU", "Россети Урал"), ("MRKV", "Россети Волга"), ("MRKY", "Россети Юг"),
    ("MRKZ", "Россети Северо-Запад"), ("MSNG", "МосЭнерго"),
    ("MSRS", "Россети Московский регион"), ("MSTT", "Мостотрест"),
    ("MTLR", "Мечел"), ("MTSS", "МТС"), ("MVID", "М.видео"),
    ("NFAZ", "НЕФАЗ"), ("NKHP", "НКХП"), ("NKNC", "Нижнекамскнефтехим"),
    ("NLMK", "НЛМК"), ("NMTP", "НМТП"), ("NSVZ", "Наука-Связь"),
    ("NVTK", "НОВАТЭК"), ("OGKB", "ОГК-2"), ("OZON", "Озон"),
    ("PHOR", "ФосАгро"), ("PIKK", "ПИК"), ("PLZL", "Полюс"),
    ("PMSB", "Пермэнергосбыт"), ("POSI", "Группа Позитив"),
    ("PRFN", "ТЕПЛАНТ"), ("RASP", "Распадская"), ("RBCM", "РБК"),
    ("RGSS", "Росгосстрах"), ("RKKE", "РКК Энергия"), ("RNFT", "РуссНефть"),
    ("ROLO", "Русолово"), ("ROSN", "Роснефть"), ("RTKM", "Ростелеком"),
    ("RUAL", "РУСАЛ"), ("RZSB", "Рязанская энергосбытовая"),
    ("SELG", "Селигдар"), ("SGZH", "Сегежа"), ("SIBN", "Газпром нефть"),
    ("SMLT", "Самолет"), ("SNGS", "Сургутнефтегаз"), ("SOFL", "Софтлайн"),
    ("SVAV", "СОЛЛЕРС"), ("SVET", "Светофор Групп"), ("TATN", "Татнефть"),
    ("TGKA", "ТГК-1"), ("TGKB", "ТГК-2"), ("TGKN", "ТГК-14"),
    ("TRMK", "ТМК"), ("TTLK", "Таттелеком"), ("UGLD", "ЮГК"),
    ("UNAC", "Объединенная авиастроительная корпорация"),
    ("UNKL", "Южно-Уральский никелевый комбинат"), ("UPRO", "Юнипро"),
    ("USBN", "Уралсиб"), ("UWGN", "ОВК"), ("VKCO", "ВК"),
    ("VRSB", "ТНС энерго Воронеж"), ("VSMO", "ВСМПО-АВИСМА"),
    ("WUSH", "ВУШ Холдинг"), ("X5", "Корпоративный центр ИКС 5"),
    ("YAKG", "Якутская топливно-энергетическая компания"),
    ("YDEX", "Яндекс"), ("ZILL", "Завод имени Лихачева"),
]

def find_company(name):
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {API_KEY}",
        "X-Secret": SECRET_KEY,
    }
    data = {"query": name, "count": 1, "status": ["ACTIVE"], "type": "LEGAL"}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code == 200:
            suggestions = r.json().get("suggestions", [])
            if suggestions:
                s = suggestions[0]
                d = s.get("data", {})
                finance = d.get("finance", {}) or {}
                return {
                    "inn": d.get("inn"),
                    "ogrn": d.get("ogrn"),
                    "full_name": d.get("name", {}).get("full_with_opf"),
                    "okved": d.get("okved"),
                    "status": d.get("state", {}).get("status"),
                    "revenue": finance.get("revenue"),
                    "income": finance.get("income"),
                    "expense": finance.get("expense"),
                    "finance_year": finance.get("year"),
                }
    except Exception as e:
        print(f"  Ошибка: {e}")
    return {}

results = []
print(f"Ищем данные по {len(companies)} компаниям через DaData...")
print("="*50)

for i, (ticker, name) in enumerate(companies):
    print(f"[{i+1}/{len(companies)}] {ticker} ({name})...", end=" ", flush=True)
    data = find_company(name)
    if data.get("inn"):
        results.append({"ticker": ticker, "search_name": name, **data})
        print(f"ИНН: {data['inn']} | ОКВЭД: {data.get('okved')} | Выручка: {data.get('revenue')}")
    else:
        results.append({"ticker": ticker, "search_name": name})
        print("не найдено")
    time.sleep(0.3)

df = pd.DataFrame(results)
df.to_csv("D:/diplom/data/companies_dadata.csv", index=False)
found_inn = df["inn"].notna().sum()
print(f"\nНайдено ИНН: {found_inn} из {len(df)}")
print(f"Сохранено: D:/diplom/data/companies_dadata.csv")