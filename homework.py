import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> None:
    """Проверяет наличие необходимых переменных окружения."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)
    if not all(tokens):
        logging.critical(
            'Отсутствует обязательная переменная окружения'
        )
        raise exceptions.TokenNotFound('Отсутствует токен.')


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram."""
    try:
        logging.debug(f'Бот начал отправлять сообщение {message}')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f"Бот успешно отправил сообщение '{message}'")
    except telegram.error.TelegramError as error:
        logging.error(f"Сбой при отправке сообщения в Telegram: {error}")


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к API и возвращает ответ."""
    request_info = {
        'endpoint': ENDPOINT,
        'params': {'from_date': timestamp},
        'headers': HEADERS,
    }
    try:
        logging.debug(
            'Бот делает запрос к API:'
            '{endpoint}; {headers}; {params}'.format(**request_info)
        )
        response = requests.get(**request_info)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.UnexpectedStatusCodeError(
                f'Cтатус ответа от {ENDPOINT} отличен от 2хх')
    except requests.RequestException as e:
        raise exceptions.UnexpectedStatusCodeError(
            f'Ошибка {e} при запросе к {ENDPOINT}')
    response_data = response.json()
    return response_data


def check_response(response: dict) -> bool:
    """Проверяет статус ответа API."""
    if not isinstance(response, dict):
        raise TypeError('Ошибка типа данных, ожидался dict')
    if 'homeworks' not in response:
        raise exceptions.EmptyResponseError(
            "В ответе остутствует список с дом. заданиями: 'homeworks'"
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError("Ошибка типа данных.")
    if 'error' in response:
        raise exceptions.UnexpectedStatusCodeError('Ошибка в ответе API')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает статус проверки работы из ответа API."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        raise KeyError("Отсутствует ключ 'homework_name' в ответе API.")

    try:
        status = homework['status']
    except KeyError:
        raise KeyError("Отсутствует ключ 'status' в ответе API.")

    if status not in HOMEWORK_VERDICTS:
        raise KeyError(f"Недокументированный статус работы: {status}")

    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    old_status = None

    while True:
        try:
            api_response = get_api_answer(timestamp)
            timestamp = api_response.get('current_date', timestamp)
            homeworks = check_response(api_response)
            if homeworks:
                last_homework = homeworks[0]
                message = parse_status(last_homework)
            else:
                message = 'Нет новых статусов работы'
            if message != old_status:
                send_message(bot, message)
                old_status = message
        except exceptions.EmptyResponseError:
            logging.error(
                "В ответе остутствует список с дом. заданиями: 'homeworks'"
            )
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            if message != old_status:
                send_message(bot, message)
                old_status = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    main()
