```dotenv
DEBUG=true
ALLOWED_HOSTS=*

DB_TYPE=POSTGRES
POSTGRES_DB=answerai
POSTGRES_USER=answeraiasjhdasd7i7fssdf
POSTGRES_PASSWORD=asdasdasddf312e
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

OPENAI_API_KEY=sk-proj-LDXXXXXXXXXX9YqXXXXXXXXXXXXXXXXXXX

WEBHOOK_URL=https://bot.domain.com/webhook/
API_DOMAIN=https://api.domain.com/check

GET_SCRIPT_URL=https://api.domain.com/get_script
GET_SCRIPT_JS=//domain.com

WEB_APP_SELECT_TIME_URL=https://bot.domain.com/select_time
WEB_APP_REDACT_TIME_URL=https://bot.domain.com/redact_time

BOT_TOKEN=834XXX869:AXXXXXXXXX
BOT_USERNAME=AiExamBot

REWERD_PER_REFFERAL=25_000
MAX_DISCOUNT=125_000
SCRIPT_BASE_PRICE=300_000
```

```nginx
# admin.domain.com
server {
    server_name admin.domain.com;

    access_log off;
    error_log /dev/null crit;
    server_tokens off;

    client_max_body_size 20M;

    location = / {
        return 302 /admin/;
    }

    location ^~ /api/ {
        return 444;
    }

    location / {
        return 404;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_redirect off;
    }

    location /static/ {
        alias /var/www/AiExamBot/staticfiles/;
        expires 30d;
        access_log off;
    }
}
```

```nginx
# domain.com
server {
    server_name domain.com;

    access_log off;
    error_log /dev/null crit;
    server_tokens off;

    client_max_body_size 5M;
    proxy_intercept_errors on;

    error_page 400 401 403 404 500 502 503 504 = /_error;

    location = /_error {
        internal;
        default_type text/plain;
        return 404;
    }

    location = / {
        return 204;
    }

    location ~ ^/([^/]+)$ {
        proxy_pass http://127.0.0.1:8000/api/v1/get_script/$1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        proxy_hide_header Server;
        add_header Server "" always;
    }
}
```

```nginx
# api.domain.com
server {
    server_name api.domain.com;

    access_log off;
    error_log /dev/null crit;
    server_tokens off;

    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;

    client_max_body_size 20M;

    location = / {
        return 204;
    }

    location / {
        proxy_pass http://127.0.0.1:8000/api/v1/;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 50s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        send_timeout 300s;

        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }

    error_page 400 401 403 404 500 502 503 504 = /__silence__;
    location = /__silence__ {
        internal;
        return 204;
    }
}
```

```nginx
# bot.domain.com
server {
    server_name bot.domain.com;

    access_log off;
    error_log /dev/null crit;
    server_tokens off;

    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/AiExamBot/staticfiles/;
        access_log off;
        log_not_found off;
        error_page 404 =404;

        expires off;
        add_header Cache-Control "no-store, no-cache, must-revalidate, max-age=0" always;
    }

    location = / {
        return 204;
    }

    location / {
        proxy_pass http://127.0.0.1:8000/api/bot/;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 50s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        send_timeout 300s;

        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }

    error_page 400 401 403 404 500 502 503 504 = /__silence__;
    location = /__silence__ {
        internal;
        return 204;
    }
}
```

```nginx
# test.domain.com
server {
    server_name test.domain.com;

    root /var/www/AiExamBot/tests/;
    index off;

    location = / {
        return 301 /index.html;
    }

    location ~ \.html$ {
        try_files $uri =404;
    }

    location / {
        return 404;
    }
}
```

```ini
[Unit]
Description=Uvicorn Django ASGI
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/AiExamBot

Environment="PYTHONUNBUFFERED=1"
Environment="DJANGO_SETTINGS_MODULE=core.settings"

ExecStart=/var/www/AiExamBot/.venv/bin/uvicorn core.asgi:application --host 127.0.0.1 --port 8000 --workers 2

Restart=always
RestartSec=3

LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```
