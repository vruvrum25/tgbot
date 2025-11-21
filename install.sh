#!/bin/bash

# Получаем папку, где лежит скрипт
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="tgbot_yandex"

echo "=========================================="
echo "   УСТАНОВКА TELEGRAM БОТА (YANDEX CPA)   "
echo "=========================================="

# 1. Обновление пакетов
echo "[1/5] Обновление системы..."
sudo apt update -qq
sudo apt install -y python3-pip python3-venv -qq

# 2. Создание Virtual Environment
echo "[2/5] Настройка Python окружения..."
if [ ! -d "$DIR/venv" ]; then
    python3 -m venv "$DIR/venv"
    echo "Virtualenv создан."
fi

# 3. Установка зависимостей
echo "[3/5] Установка библиотек..."
"$DIR/venv/bin/pip" install -r "$DIR/requirements.txt" --quiet

# 4. Настройка .env
echo "[4/5] Настройка конфига..."
if [ ! -f "$DIR/.env" ]; then
    echo "Создаю .env из шаблона..."
    cp "$DIR/.env.example" "$DIR/.env"
    
    echo ""
    echo "!!! ВНИМАНИЕ !!!"
    echo "Сейчас откроется редактор."
    echo "1. Вставь токен бота."
    echo "2. Вставь путь к папке private (где лежит leads.txt)."
    echo "Нажми любую клавишу, чтобы продолжить..."
    read -n 1 -s
    nano "$DIR/.env"
else
    echo "Файл .env уже существует, пропускаем."
fi

# 5. Настройка Systemd (Автозапуск)
echo "[5/5] Настройка автозапуска (Systemd)..."
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Генерируем файл службы
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Telegram Bot Yandex CPA
After=network.target

[Service]
User=root
WorkingDirectory=$DIR
ExecStart=$DIR/venv/bin/python3 bot.py
Restart=always
RestartSec=5
StandardOutput=append:/var/log/${SERVICE_NAME}.log
StandardError=append:/var/log/${SERVICE_NAME}.error.log

[Install]
WantedBy=multi-user.target
EOL

# Перезагрузка демонов и старт
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "=========================================="
echo "   УСТАНОВКА ЗАВЕРШЕНА!   "
echo "=========================================="
echo "Статус бота: sudo systemctl status $SERVICE_NAME"
echo "Логи бота:   tail -f /var/log/${SERVICE_NAME}.log"
