#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Запускаем сервер...${NC}"

# Запускаем сервер в фоновом режиме
python rp_handler.py --rp_serve_api > server.log 2>&1 &
SERVER_PID=$!

# Функция для корректного завершения сервера
cleanup() {
    echo -e "${YELLOW}Останавливаем сервер (PID: $SERVER_PID)...${NC}"
    kill -15 $SERVER_PID 2>/dev/null || kill -9 $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo -e "${YELLOW}Сервер остановлен.${NC}"
    exit $1
}

# Обработка сигналов для корректного завершения при прерывании скрипта
trap 'cleanup 1' SIGINT SIGTERM

# Проверяем, что процесс запустился
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}Ошибка: Не удалось запустить сервер.${NC}"
    cat server.log
    exit 1
fi

echo -e "${YELLOW}Сервер запущен с PID: $SERVER_PID${NC}"
echo -e "${YELLOW}Ожидаем запуск сервера...${NC}"

# Ждем, пока сервер полностью запустится (максимум 30 секунд)
MAX_WAIT=30
WAIT_COUNT=0
SERVER_READY=false

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    # Проверяем различные варианты сообщений о запуске
    if grep -q "Uvicorn running on http" server.log 2>/dev/null || grep -q "Running on http" server.log 2>/dev/null || grep -q "Application startup complete" server.log 2>/dev/null; then
        SERVER_READY=true
        break
    fi
    
    # Проверяем, что процесс все еще работает
    if ! ps -p $SERVER_PID > /dev/null; then
        echo -e "${RED}Ошибка: Сервер неожиданно завершил работу.${NC}"
        cat server.log
        exit 1
    fi
    
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    echo -n "."
done

echo ""

if [ "$SERVER_READY" = false ]; then
    echo -e "${RED}Ошибка: Сервер не запустился в течение $MAX_WAIT секунд.${NC}"
    cat server.log
    cleanup 1
fi

echo -e "${GREEN}Сервер успешно запущен!${NC}"
echo -e "${YELLOW}Выполняем запрос...${NC}"

# Выполняем запрос и сохраняем результат
HTTP_STATUS=$(curl -X POST http://localhost:8000/runsync \
     -H "Content-Type: application/json" \
     -d @test_input.json \
     -s -o response.txt -w "%{http_code}")
CURL_EXIT_CODE=$?

# Проверяем результат запроса
if [ $CURL_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Ошибка при выполнении запроса: код $CURL_EXIT_CODE${NC}"
    cleanup 1
elif [ $HTTP_STATUS -ge 200 ] && [ $HTTP_STATUS -lt 300 ]; then
    echo -e "${GREEN}Запрос выполнен успешно! Статус: $HTTP_STATUS${NC}"
    echo -e "${YELLOW}Ответ сервера:${NC}"
    cat response.txt
    cleanup 0
else
    echo -e "${RED}Запрос выполнен с ошибкой. Статус: $HTTP_STATUS${NC}"
    echo -e "${YELLOW}Ответ сервера:${NC}"
    cat response.txt
    cleanup 1
fi