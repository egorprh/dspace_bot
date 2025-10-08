import asyncio
from typing import Optional, Tuple

# Тип бота нужен только для подсказки типов; экземпляр бота передаётся извне
from aiogram import Bot
import random

# Импортируем наборы текстов и словари прогресс-слотов
from notification_texts import (
    WELCOME_1,
    WELCOME_2,
    PRO_WELCOME_12M,
    PRO_NEXT_DAY,
    ACCESS_ENDED_1,
    ACCESS_ENDED_2,
    DAY1_1934,
    DAY2_2022,
    DAY3_0828,
)


async def send_telegram_message(bot: Bot, telegram_id: int, message: str, max_attempts: int = 3) -> Tuple[str, Optional[str], int]:
    """
    Простая отправка сообщения с ретраями.

    Вход:
    - bot: уже инициализированный экземпляр aiogram.Bot (создаётся снаружи)
    - telegram_id: числовой chat_id получателя
    - message: текст сообщения
    - max_attempts: число попыток отправки (>=1)

    Логика:
    - Пытаемся отправить сообщение.
    - При любой ошибке запоминаем текст ошибки и повторяем попытку (пауза 0.5s),
      пока не исчерпаем лимит.

    Возврат:
    - ("sent", None, attempts_used) при успехе
    - ("failed", "текст_ошибки", attempts_used) при окончательной неудаче
    """

    last_error: Optional[str] = None
    attempts_used = 0

    for attempt in range(1, max_attempts + 1):
        attempts_used = attempt
        try:
            await bot.send_message(chat_id=telegram_id, text=message)
            return "sent", None, attempts_used
        except Exception as e:
            # Сохраняем текст ошибки (тип ошибки нам не критичен для решения — важно описание)
            last_error = str(e)
            if attempt < max_attempts:
                await asyncio.sleep(0.1)

    return "failed", last_error, attempts_used


def resolve_message_text(message_marker: str):
    """
    Возвращает фактический текст сообщения по маркеру из очереди.

    Вход:
    - message_marker: строка-маркер вида "welcome_1", "progress_slot_day1_1934" и т.п. (без фигурных скобок)

    Правила:
    - Для простых констант возвращаем соответствующий текст из notification_texts.py
    - Для прогресс-слотов (day1/day2/day3) — пока без БД и реальной логики прогресса —
      выбираем случайный вариант из словаря (none/lt3/lt5/all), чтобы иметь рабочий пример.

    Возврат:
    - Строка с текстом сообщения; если маркер не распознан — возвращаем False.

    Примечание:
    - Функция специально максимально простая: без сложных конструкций и внешних зависимостей.
    - В боевом режиме выбор текста для прогресс-слотов следует делать на основе фактического прогресса.
    """

    if not isinstance(message_marker, str):
        return False

    key = message_marker.strip()

    # Прямое соответствие константам
    simple_map = {
        "welcome_1": WELCOME_1,
        "welcome_2": WELCOME_2,
        "pro_welcome_12m": PRO_WELCOME_12M,
        "pro_next_day": PRO_NEXT_DAY,
        "access_ended_1": ACCESS_ENDED_1,
        "access_ended_2": ACCESS_ENDED_2,
    }

    if key in simple_map:
        return simple_map[key]

    # Прогресс-слоты: выбираем случайный вариант из словаря
    if key == "progress_slot_day1_1934":
        return random.choice(list(DAY1_1934.values()))
    if key == "progress_slot_day2_2022":
        return random.choice(list(DAY2_2022.values()))
    if key == "progress_slot_day3_0828":
        return random.choice(list(DAY3_0828.values()))

    # Если ничего не подошло — возвращаем False
    return False


