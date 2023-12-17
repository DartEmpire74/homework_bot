class UnexpectedStatusCodeError(Exception):
    """Исключение, обрабатывающее ошибки при запросе к API."""

    pass


class TokenNotFound(Exception):
    """Исключение, обрабатывающее ошибки переменных окружения."""

    pass


class EmptyResponseError(Exception):
    """Исключение, обрабатывающее пустой ответ API."""

    pass
