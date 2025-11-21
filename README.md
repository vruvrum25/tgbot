# Yandex Direct -> Telegram CPA Bot

Бот для приема заявок в закрытый канал, проверки на роботность (капча 2+2) и сохранения YCLID для постбэка.

## Установка на сервер

1. Клонировать репозиторий:
   `git clone https://github.com/vruvrum25/repo.git /root/my_bot`

2. Зайти в папку:
   `cd /root/my_bot`

3. Запустить установщик:
   `chmod +x install.sh && ./install.sh`

## Структура файлов в папке private/
Бот ожидает, что PHP создает файл `leads.txt` в формате JSON Lines:
`{"hash": "invite_hash", "yclid": "123456"}`

Бот создает файл `to_send_yandex.txt` с проверенными лидами:
`USER_ID|YCLID|verified|DATETIME`
