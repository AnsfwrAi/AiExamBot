## routers
```chef
WEBHHOK_URL=bot.domain/bot/webhook and original bot.endpoint /api/bot/webhook

API_DOMAIN=api.domain/api/v1/check this domain for .js file важно чтоб все остальные эндпоинты были скрытыми

GET_SCRIPT_URL=domain/<name.js> тут важно чтоб был первый эндпоинт оригинальный эндпоинт/api/v1/get_script

GET_SCRIPT_JS=domain/<name.js> тут важно чтоб был первый эндпоинт оригинальный эндпоинт/api/v1/get_script

WEB_APP_SELECT_TIME_URL=bot.domain/bot/select_time тут для вебапп а это оригинальный эндпоинт/api/bot/select_time

WEB_APP_REDACT_TIME_URL=bot.domain/bot/redact_time тут для редичинга /api/bot/redact_time

BOT_TOKEN=tg_bot_token
BOT_USERNAME=botusername без @
```

---
# Base settings
```dotenv
#DEBUG=if vlue in ['true', '1', 't', 'y', 'yes'] = True, False
DEBUG=True
ALLOWED_HOSTS=*
# Database settings

# DB_TYPE=POSTGRES / SQLITE
DB_TYPE=POSTGRES

POSTGRES_DB=a
POSTGRES_USER=a
POSTGRES_PASSWORD=a
POSTGRES_HOST=localhost
POSTGRES_PORT=5432


# OpenAI settings
OPENAI_API_KEY=sk-projT3........

WEBHOOK_URL=https://1234dfasddss.ngrok-free.app/api/bot/webhook
API_DOMAIN=https://1234dfasddss.ngrok-free.app/api/v1/check

GET_SCRIPT_URL=https://1234dfasddss.ngrok-free.app/api/v1/get_script
GET_SCRIPT_JS=https://1234dfasddss.ngrok-free.app

WEB_APP_SELECT_TIME_URL=https://1234dfasddss.ngrok-free.app/api/bot/select_time
WEB_APP_REDACT_TIME_URL=https://1234dfasddss.ngrok-free.app/api/bot/redact_time

BOT_TOKEN=803343224:AA.....
BOT_USERNAME=HijachAnsfwerAiBot


#CONSTS
REWERD_PER_REFFERAL=25_000
MAX_DISCOUNT=125_000
SCRIPT_BASE_PRICE=300_000
```
---
```bash
cp .env.exm .env # create your own .env file and fill it with your settings
```
```bash
python3 -m venv .venv # create virtual environment
```
```bash
source .venv/bin/activate # activate virtual environment
```
```bash
pip install -r requirements.txt # install dependencies
```
```bash
ptrhon manage.py makemigrations # create migrations
```
```bash
python manage.py migrate # apply migrations
```
```bash
python manage.py createsuperuser # create superuser
```
```bash
python manage.py setup_webhook # setup webhook for telegram bot
```
```bash
uvicorn core.asgi:application --workers 1 # run the application
```

