# Дипломная работа — анализ российского фондового рынка

Набор Python-скриптов для сбора, очистки и эконометрического анализа данных
по акциям российских компаний (недельные цены, фундаментальные показатели,
панельные регрессии, кластеризация).

## Структура

Скрипты пронумерованы в порядке выполнения пайплайна:

| Этап | Скрипты | Назначение |
|------|---------|------------|
| Сбор данных | `01_download_prices.py`, `09_get_inn_dadata.py`, `10_parse_cbonds.py`, `get_cbr_fx.py`, `get_fx_rates.py`, `get_inn.py`, `get_market_cap.py` | Загрузка цен, ИНН, облигаций, курсов валют |
| Очистка | `02_check_data.py`, `03_clean_data.py`, `12_clean_fundamentals.py`, `13_final_clean.py` | Проверка и очистка сырых данных |
| Признаки | `04_detect_events.py`, `05_add_yndx.py`, `06_momentum.py`, `07_add_redomiciled.py`, `11_convert_currency.py`, `14_final_convert.py` | Расчёт событий, моментума, конвертация валют |
| Панель | `15_build_panel.py` | Сборка панельных данных |
| Анализ | `20_regression.py`, `21_robustness.py`, `22_sector_analysis.py`, `23_kmeans.py`, `28_descriptive_stats.py` | Регрессии, робастность, секторный анализ, кластеризация |
| Утилиты | `check_*.py`, `fix_*.py`, `diagnose_all.py`, `print_*.py` | Вспомогательные проверки и диагностика |

> Папки `data/` и `outputs/` в репозиторий не включены (см. `.gitignore`).
> Скрипты ожидают их наличия локально.

## Установка

```bash
pip install -r requirements.txt
```

## Секреты

Скрипт `09_get_inn_dadata.py` использует API [DaData](https://dadata.ru/).
Ключи задаются через переменные окружения:

```bash
export DADATA_API_KEY=ваш_ключ
export DADATA_SECRET_KEY=ваш_секрет
```

## Примечание

Часть скриптов содержит абсолютные пути вида `D:/diplom/...` (Windows).
При запуске на другой машине пути нужно скорректировать.
