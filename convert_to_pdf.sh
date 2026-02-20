#!/bin/bash
# Скрипт для конвертации HTML в PDF через браузер

HTML_FILE="/Users/annarybkina/Desktop/Allio/ИИ Цены/Динамика_обращений_2025.html"
PDF_FILE="/Users/annarybkina/Desktop/Allio/ИИ Цены/Динамика_обращений_2025.pdf"

# Открываем в Safari
open -a Safari "$HTML_FILE"

echo "HTML файл открыт в Safari"
echo "Для создания PDF:"
echo "1. Нажмите Cmd+P (Печать)"
echo "2. Внизу слева нажмите 'PDF' -> 'Сохранить как PDF'"
echo "3. Сохраните как: $PDF_FILE"
