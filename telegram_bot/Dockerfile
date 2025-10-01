# Базовый Python-образ
FROM python:3.11-slim

# Установка зависимостей системы, это необязательно
# RUN apt-get update && apt-get install -y \
#     gcc \
#     libffi-dev \
#     libssl-dev \
#     libxml2-dev \
#     libxslt-dev \
#     libjpeg-dev \
#     zlib1g-dev \
#     && rm -rf /var/lib/apt/lists/*

# Создание директории приложения
WORKDIR /app

# Копируем проект
COPY . .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка переменной окружения
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "bot.py"]

# TODO На сервере добавить включение докера (автозагрузка): systemctl enable docker.service
# Установка докера https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04-ru