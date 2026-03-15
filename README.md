# Steam Price Watcher

Бот отслеживает предметы в указанном Steam-инвентаре и отправляет уведомления в Telegram при изменении рыночной цены на заданный процент (X%). Удобно ловить пампы дешёвых скинов.

## Требования

- Python 3.10+ (или Docker)
- Источник данных Steam (один из двух):
  - **steamapis** — [SteamApis](https://steamapis.com): один ключ, мало запросов, но бесплатный лимит маленький
  - **steam_official** — без ключа: инвентарь через [Steam Community Inventory](https://steamcommunity.com/inventory), цены через запросы к маркету по каждому предмету (с паузой между запросами)
- Telegram-бот (токен от @BotFather) и chat_id для уведомлений

## Запуск в Docker (рекомендуется)

```bash
cp .env.example .env
# Отредактируйте .env (STEAM_PROVIDER, ключи API, TELEGRAM_*, STEAM_ID, APP_ID и т.д.)

# Сборка и запуск в фоне (цикл с интервалом из конфига)
docker compose up -d --build

# Один проход и выход
docker compose run --rm watcher python main.py --once

# Логи
docker compose logs -f watcher
```

Данные SQLite сохраняются в каталоге `./data` на хосте (volume в docker-compose).

## Установка без Docker

```bash
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env: STEAM_PROVIDER, ключ API, TELEGRAM_*, STEAM_ID, APP_ID, THRESHOLD_PERCENT
```

## Запуск без Docker

- Один проход (проверить инвентарь и цены один раз):
  ```bash
  python main.py --once
  ```
- Непрерывный режим с интервалом из конфига (по умолчанию 10 минут):
  ```bash
  python main.py
  ```

## Конфигурация (.env)

| Переменная | Описание |
|------------|----------|
| `STEAM_PROVIDER` | `steamapis` или `steam_official` |
| `STEAM_API_KEY` | Ключ SteamApis (обязателен при `STEAM_PROVIDER=steamapis`) |
| `STEAM_WEB_API_KEY` | Не используется для `steam_official` (можно не задавать) |
| `TELEGRAM_BOT_TOKEN` | Токен бота Telegram |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений |
| `STEAM_ID` | Steam ID 64 (инвентарь для отслеживания) |
| `APP_ID` | ID игры (730 = CS2, 570 = Dota 2) |
| `THRESHOLD_PERCENT` | Порог изменения цены в % для уведомления |
| `POLL_INTERVAL_MINUTES` | Интервал опроса в минутах |
| `NOTIFY_ON_DROP` | Уведомлять при падении цены (true/false) |
| `MIN_PRICE_USD` | Минимальная цена в USD для уведомлений (0 = без фильтра) |

## Структура

- `config/` — настройки из .env
- `steam/` — провайдеры инвентаря и цен (SteamApis или Steam Official)
- `storage/` — хранение последних цен (SQLite)
- `notifier/` — отправка в Telegram
- `watcher/` — цикл: инвентарь → цены → сравнение → уведомления
