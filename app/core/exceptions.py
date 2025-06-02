class ExchangeError(Exception):
    """Ошибка, связанная с работой биржи или API обмена."""
    pass

class RateLimitError(Exception):
    """Ошибка превышения лимита запросов к API."""
    pass 