#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для модификации файла Кинопарк:
- Увеличивает стоимость на 5% в половине квартир (случайно выбранных)
- Удаляет 10% квартир (случайно выбранных)
- Добавляет несколько выбросов снизу (квартиры с заниженной стоимостью)
"""

import csv
import random

def modify_kinopark_file(input_file, output_file):
    """Модифицирует файл Кинопарк"""
    
    # Читаем исходный файл
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f'Исходное количество квартир: {len(rows)}')
    
    # Устанавливаем seed для воспроизводимости (можно убрать для полной случайности)
    random.seed()
    
    # Шаг 1: Увеличиваем стоимость на 5% в половине квартир
    rows_to_modify = random.sample(rows, len(rows) // 2)
    modified_count = 0
    
    for row in rows_to_modify:
        стоимость = row.get('Стоимость', '').strip()
        if стоимость:
            try:
                # Убираем пробелы и преобразуем в число
                стоимость_чистая = стоимость.replace(' ', '').replace('\xa0', '')
                стоимость_num = int(float(стоимость_чистая))
                
                # Увеличиваем на 5%
                новая_стоимость = int(стоимость_num * 1.05)
                
                # Форматируем обратно с пробелами (как в исходном файле)
                новая_стоимость_строка = f"{новая_стоимость:,}".replace(',', ' ')
                row['Стоимость'] = новая_стоимость_строка
                modified_count += 1
            except (ValueError, TypeError):
                pass
    
    print(f'Увеличена стоимость на 5% в {modified_count} квартирах')
    
    # Шаг 2: Удаляем 10% квартир
    rows_to_delete = random.sample(rows, len(rows) // 10)
    for row in rows_to_delete:
        rows.remove(row)
    
    deleted_count = len(rows_to_delete)
    print(f'Удалено {deleted_count} квартир')
    
    # Шаг 3: Добавляем несколько выбросов снизу (квартиры с заниженной стоимостью)
    # Берем 5-10 случайных квартир и уменьшаем их стоимость на 30-50%
    num_outliers = min(10, len(rows) // 20)  # Примерно 5% от оставшихся, но не более 10
    rows_for_outliers = random.sample(rows, num_outliers)
    outliers_count = 0
    
    for row in rows_for_outliers:
        стоимость = row.get('Стоимость', '').strip()
        if стоимость:
            try:
                # Убираем пробелы и преобразуем в число
                стоимость_чистая = стоимость.replace(' ', '').replace('\xa0', '')
                стоимость_num = int(float(стоимость_чистая))
                
                # Уменьшаем на случайный процент от 30% до 50%
                reduction_percent = random.uniform(0.30, 0.50)
                новая_стоимость = int(стоимость_num * (1 - reduction_percent))
                
                # Форматируем обратно с пробелами
                новая_стоимость_строка = f"{новая_стоимость:,}".replace(',', ' ')
                row['Стоимость'] = новая_стоимость_строка
                outliers_count += 1
            except (ValueError, TypeError):
                pass
    
    print(f'Создано {outliers_count} выбросов снизу (стоимость уменьшена на 30-50%)')
    print(f'Итоговое количество квартир: {len(rows)}')
    
    # Сохраняем в новый файл
    if rows:
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = ['Этаж', 'Комнатность', 'Общая площадь', 'Отделка', 'Стоимость', 'Вид из окна']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f'✓ Файл сохранен: {output_file}')
        return True
    else:
        print('Ошибка: не осталось квартир для сохранения')
        return False

if __name__ == '__main__':
    input_file = '/Users/annarybkina/Desktop/Сравнение цен/bnMAP_pro_Прайс_листы_Санкт_Петербург - Кинопарк.csv'
    output_file = '/Users/annarybkina/Desktop/Сравнение цен/bnMAP_pro_Прайс_листы_Санкт_Петербург - Кинопарк_модифицированный.csv'
    modify_kinopark_file(input_file, output_file)

