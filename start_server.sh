#!/bin/bash
# Скрипт запуска обоих серверов Flask параллельно

cd "$(dirname "$0")"

echo "Запуск основного сервера на http://localhost:5001"
echo "Запуск сервера логов на http://localhost:5002/logs"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Запускаем оба сервера в фоне
python3 app.py &
APP_PID=$!

python3 logs_server.py &
LOGS_PID=$!

# Функция для остановки серверов при выходе
cleanup() {
    echo ""
    echo "Остановка серверов..."
    kill $APP_PID 2>/dev/null
    kill $LOGS_PID 2>/dev/null
    exit 0
}

# Перехватываем сигналы для корректной остановки
trap cleanup SIGINT SIGTERM

# Ждем завершения процессов
wait
