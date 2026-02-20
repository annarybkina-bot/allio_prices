#!/bin/bash
# Скрипт для запуска обоих серверов параллельно

cd "$(dirname "$0")"

# Останавливаем старые процессы на портах 5001 и 5002
echo "Остановка старых процессов..."
lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null
lsof -ti:5002 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

echo ""
echo "=========================================="
echo "Запуск серверов..."
echo "=========================================="
echo ""
echo "Основной сервер: http://localhost:5001"
echo "  - Главная страница: http://localhost:5001/"
echo "  - Прототип: http://localhost:5001/prototype"
echo ""
echo "Сервер логов: http://localhost:5002/logs"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "=========================================="
echo ""

# Запускаем оба сервера в фоне
python3 app.py > /dev/null 2>&1 &
APP_PID=$!

python3 logs_server.py > /dev/null 2>&1 &
LOGS_PID=$!

# Ждем немного, чтобы серверы запустились
sleep 2

# Проверяем, что серверы запустились
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "✓ Основной сервер запущен (PID: $APP_PID)"
else
    echo "✗ Ошибка: основной сервер не запустился"
fi

if lsof -ti:5002 > /dev/null 2>&1; then
    echo "✓ Сервер логов запущен (PID: $LOGS_PID)"
else
    echo "✗ Ошибка: сервер логов не запустился"
fi

echo ""
echo "Серверы работают. Откройте в браузере:"
echo "  http://localhost:5001/prototype"
echo "  http://localhost:5002/logs"
echo ""

# Функция для остановки серверов при выходе
cleanup() {
    echo ""
    echo "Остановка серверов..."
    kill $APP_PID 2>/dev/null
    kill $LOGS_PID 2>/dev/null
    lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null
    lsof -ti:5002 2>/dev/null | xargs kill -9 2>/dev/null
    echo "Серверы остановлены."
    exit 0
}

# Перехватываем сигналы для корректной остановки
trap cleanup SIGINT SIGTERM

# Ждем завершения процессов
wait
