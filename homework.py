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

PREV_HOMEWORK_STATUS = None


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout)


def check_tokens() -> None:
    """Проверяет наличие необходимых переменных окружения."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)
    for token in tokens:
        if token is None:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: "{token}"'
            )
            raise exceptions.TokenNotFound(f'Отсутсвует токен "{token}"')


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f"Бот отправил сообщение '{message}'")
    except Exception:
        logging.error("Сбой при отправке сообщения в Telegram")


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к API и возвращает ответ."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params={
            'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            logging.error(f'Проблема с доступом к {ENDPOINT}')
            raise exceptions.UnexpectedStatusCodeError(
                f'Cтатус ответа от {ENDPOINT} отличен от 2хх')
    except Exception as e:
        logging.error(f'Ошибка {e} при запросе к {ENDPOINT}')
        raise exceptions.UnexpectedStatusCodeError(
            f'Ошибка {e} при запросе к {ENDPOINT}')
    response_data = response.json()
    return response_data


def check_response(response: dict) -> bool:
    """Проверяет статус ответа API."""
    if not isinstance(response, dict):
        logging.error('Ошибка типа данных, ожидался dict')
        raise TypeError('Ошибка типа данных, ожидался dict')
    if 'homeworks' not in response:
        logging.error("В ответе отсутсвует ключ 'homeworks'")
        raise KeyError("В ответе отсутсвует ключ 'homeworks'")
    if not isinstance(response['homeworks'], list):
        logging.error("Ошибка типа данных.")
        raise TypeError("Ошибка типа данных.")
    if 'error' in response:
        logging.error(f"Ошибка в ответе API: {response['error']}")
        return False
    return True


def parse_status(homework: dict) -> str:
    """Извлекает статус проверки работы из ответа API."""
    global PREV_HOMEWORK_STATUS

    try:
        homework_name = homework['homework_name']
    except KeyError:
        logging.error("Отсутствует ключ 'homework_name' в ответе API.")
        raise KeyError("Отсутствует ключ 'homework_name' в ответе API.")

    try:
        status = homework['status']
    except KeyError:
        logging.error("Отсутствует ключ 'status' в ответе API.")
        raise KeyError("Отсутствует ключ 'status' в ответе API.")

    if status not in HOMEWORK_VERDICTS:
        logging.error(f"Недокументированный статус работы: {status}")
        raise KeyError(f"Недокументированный статус работы: {status}")

    verdict = HOMEWORK_VERDICTS[status]
    if verdict is None or verdict != PREV_HOMEWORK_STATUS:
        PREV_HOMEWORK_STATUS = verdict
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.debug('Статус проверки работы не изменился')
        return "Статус работы не изменился"


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            api_response = get_api_answer(timestamp)
            if (check_response(api_response)
               and len(api_response['homeworks']) >= 1):
                message = parse_status(api_response['homeworks'][0])
                send_message(bot, message)
        except Exception as error:
            logging.error(f"Сбой в работе программы: {error}")
            message = f"Сбой в работе программы: {error}"
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
