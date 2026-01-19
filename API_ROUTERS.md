
- **Public URL** — то, что видит внешний мир
- **Internal Endpoint** — реальный API, скрытый от глаз
- Публичные маршруты работают как прокси / маски
- Внутренняя структура API нигде не светится

---

## 1. Telegram Webhook

### Public URL
```

POST [https://bot.domain/bot/webhook](https://bot.domain/bot/webhook)

```

### Internal Endpoint
```

POST /api/bot/webhook

```

Назначение:
- Прием апдейтов от Telegram
- Публичный URL проксирует запросы во внутренний API

---
## 2. API Domain (AI Image Check)

### Public URL
POST https://api.domain/api/v1/check

### Назначение
Публичный эндпоинт для проверки изображения через AI.

Принимает данные от клиентского `.js`-скрипта и:
- валидирует `key`
- проверяет `fingerprint`
- обрабатывает изображение
- возвращает AI-ответ

---

### Request (multipart / form-data)

| Field        | Type   | Description                                  |
|-------------|--------|----------------------------------------------|
| image       | file   | Изображение для анализа                      |
| key         | string | Ключ скрипта                                 |
| fingerprint | string | Идентификатор клиента (антиабьюз / защита)  |

---

### Response

- `200 / 201` — AI-ответ успешно получен
- `403` — fingerprint невалиден
- `404` — скрипт не найден или неактивен
- `429` — превышен лимит использования
- `500` — ошибка AI обработки

---

### Ограничения и безопасность

- Эндпоинт **не является общим API**
- Используется **только** клиентским `.js`
- ❌ нет CRUD-доступа
- ❌ нет списков, методов, схем
- ❌ ошибки не раскрывают внутреннюю структуру
- ✔️ доступ строго по `key`
- ✔️ fingerprint используется для привязки клиента
- ✔️ лимиты и временные окна обязательны

---

### Примечание

Этот домен предназначен **исключительно** для AI-проверки изображений.  
Любые другие запросы или попытки исследования API должны:
- возвращать 404
- не логироваться наружу
- не раскрывать архитектуру проекта
---

## 3. Get Script (JavaScript Loader)

### Public URL
```

GET [https://domain/](https://domain/)<name>.js

```

### Internal Endpoint
```

GET /api/v1/get_script

```

Правила:
- `<name>.js` — публичная маска
- Реальный API `/api/v1/get_script` полностью скрыт
- Используется для подключения скриптов на сторонних сайтах

---

## 4. WebApp — Select Time

### Public URL
```

POST [https://bot.domain/bot/select_time](https://bot.domain/bot/select_time)

```

### Internal Endpoint
```

POST /api/bot/select_time

```

Назначение:
- Выбор времени через Telegram WebApp

---

## 5. WebApp — Redact Time

### Public URL
```

POST [https://bot.domain/bot/redact_time](https://bot.domain/bot/redact_time)

```

### Internal Endpoint
```

POST /api/bot/redact_time

```

Назначение:
- Редактирование времени через Telegram WebApp

---

## 6. Общая таблица маршрутов

| Feature          | Public URL                | Internal Endpoint          |
|------------------|---------------------------|----------------------------|
| Webhook          | /bot/webhook              | /api/bot/webhook           |
| JS Check Domain  | /api/v1/check             | JS only                    |
| Get Script (.js) | /<name>.js                | /api/v1/get_script         |
| Select Time      | /bot/select_time          | /api/bot/select_time       |
| Redact Time      | /bot/redact_time          | /api/bot/redact_time       |

---

## 7. Security Rules (не обсуждается)

- Внешний мир **не знает**, что у тебя есть `/api/*`
- Все публичные маршруты — прокси или маски
- API Domain отдает **только `.js`**
- Любые другие запросы:
  - 404
  - без описаний
  - без логов наружу
- Чем меньше информации — тем дольше живет проект

---

## 8. Итоговая логика

```

Client
↓
Public URL (mask)
↓
Internal API (/api/*)

```

Если кто-то видит реальный API — значит где-то накосячили.
```
