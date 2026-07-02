#!/bin/bash
set -e

echo "=== Запуск проекта на слабом сервере (пошаговый запуск) ==="

echo "--> 1. Запуск базы данных Postgres..."
docker compose up -d db
echo "Ожидаем инициализации Postgres (10 секунд)..."
sleep 10

echo "--> 2. Запуск кэш-сервера Redis..."
docker compose up -d redis
echo "Ожидаем инициализации Redis (5 секунд)..."
sleep 5

echo "--> 3. Сборка и запуск Django (веб-приложения)..."
docker compose up -d --build web
echo "Ожидаем применения миграций и установки вебхука (12 секунд)..."
sleep 12

echo "--> 4. Запуск веб-сервера Caddy (SSL)..."
docker compose up -d caddy

echo "=== Все контейнеры успешно запущены по очереди! ==="
docker compose ps
