FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости для Pillow и шрифтов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY pyproject.toml README.md ./

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir .

# Копируем весь проект (кроме того, что в .dockerignore)
COPY . .

# Создаём необходимые папки
RUN mkdir -p output logs app/data

# Команда запуска
CMD ["python", "-m", "app.main"]