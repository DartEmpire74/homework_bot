## Описание проекта 
Телеграмм бот для отслеживания статуса проверки учебных проектов. 

### Стек технологий
- Python 3.9
- Telegram Bot API

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```
cd homework_bot
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
source env/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Создать .env файл в корне проекта со следующими переменными:
```
PRACTICUM_TOKEN - токен Яндекс Практикума 
TELEGRAM_TOKEN - токен вашего личного аккаунта телеграм
TELEGRAM_CHAT_ID - токен вашего бота в телеграм
```

Запустить бота 
```
python homework.py
```
