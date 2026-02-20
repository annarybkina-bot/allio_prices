#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для преобразования файла Залив.csv в правильный формат
"""

import csv

def convert_zaliv_file(input_file, output_file):
    """Преобразует файл Залив в правильный формат"""
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        output_rows = []
        
        for row in reader:
            # Фильтруем только квартиры (не кладовки)
            тип_объекта = row.get('Тип объекта', '').strip()
            if тип_объекта == 'Кладовка':
                continue
            
            # Извлекаем нужные поля
            этаж = row.get('Этаж', '').strip()
            число_комнат = row.get('Число комнат', '').strip()
            площадь_общая = row.get('Площадь общая', '').strip()
            стоимость = row.get('Стоимость, руб', '').strip()
            вид_из_окна = row.get('Вид из окна', '').strip()
            
            # Пропускаем строки с пустыми критическими полями
            if not all([этаж, число_комнат, площадь_общая, стоимость]):
                continue
            
            # Преобразуем комнатность
            try:
                комнатность_num = int(float(число_комнат.replace(',', '.')))
                комнатность = f"{комнатность_num}к"
            except (ValueError, TypeError):
                continue
            
            # Преобразуем площадь
            площадь = площадь_общая.replace(',', '.')
            
            # Преобразуем стоимость (убираем пробелы)
            стоимость_чистая = стоимость.replace(' ', '').replace('\xa0', '')
            
            # Проверяем, что стоимость - число
            try:
                float(стоимость_чистая)
            except ValueError:
                continue
            
            # Преобразуем вид из окон
            вид = вид_из_окна if вид_из_окна else 'На улицу'
            
            output_rows.append({
                'Этаж': этаж,
                'Комнатность': комнатность,
                'Вид из окон': вид,
                'Стоимость': стоимость_чистая,
                'Общая площадь (м.кв.)': площадь
            })
        
        # Сохраняем в новый файл
        if output_rows:
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = ['Этаж', 'Комнатность', 'Вид из окон', 'Стоимость', 'Общая площадь (м.кв.)']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(output_rows)
            
            print(f'✓ Преобразовано {len(output_rows)} квартир')
            print(f'✓ Файл сохранен: {output_file}')
            return True
        else:
            print('Не найдено квартир для преобразования')
            return False

if __name__ == '__main__':
    input_file = '/Users/annarybkina/Downloads/bnMAP_pro_Прайс_листы_Санкт_Петербург - Залив.csv'
    output_file = '/Users/annarybkina/Desktop/Allio/ИИ Цены/Залив.csv'
    convert_zaliv_file(input_file, output_file)

