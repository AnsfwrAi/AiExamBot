#!/bin/bash
set -e

# Wait for Postgres if DB_TYPE is POSTGRES
if [ "$DB_TYPE" = "POSTGRES" ]; then
  echo "--> Waiting for Postgres database to start..."
  python -c "
import sys
import time
import psycopg2
import os

db_name = os.getenv('POSTGRES_DB', 'answer_ai')
db_user = os.getenv('POSTGRES_USER', 'answer_ai')
db_pass = os.getenv('POSTGRES_PASSWORD', 'answer_ai')
db_host = os.getenv('POSTGRES_HOST', 'db')
db_port = os.getenv('POSTGRES_PORT', '5432')

for i in range(30):
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        conn.close()
        print('Postgres is ready!')
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f'Postgres is unavailable, waiting... ({i+1}/30)')
        time.sleep(1)
print('Postgres connection timed out!')
sys.exit(1)
"
fi

echo "--> Applying database migrations..."
python manage.py migrate --noinput

if [ -n "$BOT_TOKEN" ] && [ -n "$WEBHOOK_URL" ]; then
  echo "--> Setting up Telegram Webhook..."
  python manage.py setup_webhook || echo "Failed to set up webhook, continuing..."
else
  echo "--> BOT_TOKEN or WEBHOOK_URL is not set, skipping webhook setup"
fi

echo "--> Starting ASGI Application..."
exec uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --workers 1
