FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое папки backend в корень /app
COPY backend/ .

# Запускаем приложение (теперь оно в корне /app, поэтому просто app:app)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]