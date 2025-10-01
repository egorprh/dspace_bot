import logging
from logging.handlers import TimedRotatingFileHandler

# Настройки
LOG_FILENAME = "logs/app.log"
LOG_LEVEL = logging.INFO
LOG_INTERVAL_MONTHS = 1
BACKUP_COUNT = 3  # Сколько архивов хранить

# Создание логгера
logger = logging.getLogger("dept_bot_logger")
logger.setLevel(LOG_LEVEL)

# Формат вывода
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# === Хендлер для ротации по времени ===
file_handler = TimedRotatingFileHandler(
    filename=LOG_FILENAME,
    when="M",              # Ротация раз в месяц
    interval=LOG_INTERVAL_MONTHS,
    backupCount=BACKUP_COUNT,
    encoding="utf-8",
    utc=True
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# === Хендлер для консоли ===
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
