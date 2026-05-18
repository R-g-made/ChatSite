@echo off
chcp 65001 > nul
echo 1.Зависимости бэка
call .venv\Scripts\activate
pip install -r backend/requirements.txt

echo 2.Зависимости фронта
cd frontend
call npm install
cd ..

echo 3.Новое окно бэк
start cmd /k "call .venv\Scripts\activate && python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000"

echo 4.Новое окно фронт
start cmd /k "cd frontend && npm run dev -- --host 127.0.0.1"

echo Все команды запущены Бэк: http://127.0.0.1:8000, Фронт: http://127.0.0.1:5173 (или 5174)
pause
