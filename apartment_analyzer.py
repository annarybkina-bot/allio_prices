#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа и группировки квартир по сопоставимым параметрам
"""

import csv
import re
from pathlib import Path
from collections import defaultdict


def normalize_floor(floor):
    """Нормализует этаж: первый (1) или не первый (>1)"""
    try:
        floor_num = int(float(str(floor)))
        return "первый" if floor_num == 1 else "не первый"
    except (ValueError, TypeError):
        return "не первый"


def normalize_rooms(rooms):
    """Нормализует комнатность"""
    if not rooms or str(rooms).strip() == '':
        return None
    rooms_str = str(rooms).strip().lower()
    
    # Обрабатываем студию как 1 комнату
    if 'студи' in rooms_str:
        return "1к"
    
    # Убираем все кроме цифр и "к"
    rooms_str = re.sub(r'[^\dк]', '', rooms_str)
    # Извлекаем число комнат
    match = re.search(r'(\d+)', rooms_str)
    if match:
        return f"{match.group(1)}к"
    return rooms_str


def normalize_view(view):
    """Нормализует вид из окон: во двор или на улицу"""
    if not view or str(view).strip() == '':
        return None
    view_str = str(view).strip().lower()
    
    # Если содержит "во двор" и не содержит "на улицу" - во двор
    if "во двор" in view_str and "на улицу" not in view_str:
        return "во двор"
    # Если содержит "на улицу" - на улицу
    elif "на улицу" in view_str:
        return "на улицу"
    # Если содержит оба варианта - на улицу (приоритет)
    elif "во двор" in view_str:
        return "на улицу"
    else:
        return "на улицу"  # По умолчанию


def normalize_area(area):
    """Нормализует площадь и группирует с шагом 10 м² (например, 40-50)"""
    if not area or str(area).strip() == '':
        return None
    try:
        # Заменяем запятую на точку для парсинга
        area_str = str(area).replace(',', '.')
        area_float = float(area_str)
        # Определяем нижнюю границу диапазона (например, 50.5 -> 50, 55.2 -> 50, 65.8 -> 60)
        lower_bound = int(area_float // 10) * 10
        upper_bound = lower_bound + 10
        return f"{lower_bound}-{upper_bound}"
    except (ValueError, TypeError):
        return None


def normalize_price(price):
    """Нормализует стоимость"""
    if not price or str(price).strip() == '':
        return None
    try:
        # Убираем все пробелы (разделители тысяч) и другие нечисловые символы, кроме точки и запятой
        price_str = str(price).strip().replace(' ', '').replace('\xa0', '')  # \xa0 - неразрывный пробел
        # Заменяем запятую на точку для парсинга
        price_str = price_str.replace(',', '.')
        return int(float(price_str))
    except (ValueError, TypeError):
        return None


def load_and_normalize_csv(file_path):
    """Загружает CSV файл и нормализует данные"""
    apartments = []
    
    encodings = ['utf-8', 'cp1251', 'windows-1251']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Нормализуем названия колонок (убираем пробелы в начале и конце)
                    normalized_row = {k.strip(): v for k, v in row.items()}
                    
                    # Нормализуем данные
                    floor_norm = normalize_floor(normalized_row.get('Этаж', ''))
                    rooms_norm = normalize_rooms(normalized_row.get('Комнатность', ''))
                    
                    # Поддержка альтернативных названий колонок
                    view_norm = normalize_view(
                        normalized_row.get('Вид из окон', '') or 
                        normalized_row.get('Вид из окна', '')
                    )
                    area_norm = normalize_area(
                        normalized_row.get('Общая площадь (м.кв.)', '') or 
                        normalized_row.get('Общая площадь', '')
                    )
                    price_norm = normalize_price(normalized_row.get('Стоимость', ''))
                    
                    # Пропускаем строки с пустыми критическими полями
                    if not all([floor_norm, rooms_norm, view_norm, area_norm is not None, price_norm is not None]):
                        continue
                    
                    apartments.append({
                        'Этаж': normalized_row.get('Этаж', ''),
                        'Комнатность': normalized_row.get('Комнатность', ''),
                        'Вид из окон': normalized_row.get('Вид из окон', '') or normalized_row.get('Вид из окна', ''),
                        'Площадь': normalized_row.get('Общая площадь (м.кв.)', '') or normalized_row.get('Общая площадь', ''),
                        'Стоимость_норм': price_norm,
                        'Этаж_норм': floor_norm,
                        'Комнатность_норм': rooms_norm,
                        'Вид_норм': view_norm,
                        'Площадь_норм': area_norm
                    })
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {e}")
            return []
    
    return apartments


def group_apartments(apartments, source_name):
    """Группирует квартиры по сопоставимым параметрам"""
    groups = defaultdict(list)
    
    for apt in apartments:
        group_key = (
            apt['Комнатность_норм'],
            apt['Этаж_норм'],
            apt['Вид_норм'],
            apt['Площадь_норм']
        )
        
        groups[group_key].append({
            'Этаж': apt['Этаж'],
            'Комнатность': apt['Комнатность'],
            'Вид из окон': apt['Вид из окон'],
            'Площадь': apt['Площадь'],
            'Стоимость': apt['Стоимость_норм'],
            'Источник': source_name
        })
    
    # Сортируем квартиры по стоимости внутри каждой группы
    for group_key in groups:
        groups[group_key].sort(key=lambda x: x['Стоимость'])
    
    return groups


def get_floor_range(apartments):
    """Получает диапазон этажей в группе"""
    floors = []
    for apt in apartments:
        try:
            floor_num = int(float(str(apt['Этаж'])))
            floors.append(floor_num)
        except (ValueError, TypeError):
            continue
    
    if not floors:
        return "нет данных"
    
    min_floor = min(floors)
    max_floor = max(floors)
    
    if min_floor == max_floor:
        return str(min_floor)
    else:
        return f"{min_floor}-{max_floor}"


def save_groups_summary_to_csv(all_groups_dict, output_path):
    """Сохраняет сводку всех групп в один CSV файл (только список групп, без деталей квартир)"""
    all_rows = []
    
    for source_name, groups in all_groups_dict.items():
        # Сортируем группы для красивого вывода
        def sort_key(group_item):
            комнатность, этаж, вид, площадь = group_item[0]
            # Извлекаем нижнюю границу площади для сортировки
            area_lower = int(площадь.split('-')[0]) if '-' in площадь else 0
            return (комнатность, этаж, вид, area_lower)
        
        sorted_groups = sorted(groups.items(), key=sort_key)
        
        for group_key, apartments in sorted_groups:
            комнатность, этаж, вид, площадь = group_key
            
            # Вычисляем статистику по стоимости
            costs = [apt['Стоимость'] for apt in apartments]
            min_cost = min(costs)
            max_cost = max(costs)
            avg_cost = int(sum(costs) / len(costs))
            
            all_rows.append({
                'Источник': source_name,
                'Комнатность': комнатность,
                'Этаж': этаж,
                'Вид': вид,
                'Площадь_диапазон': f"{площадь} м²",
                'Количество_квартир': len(apartments),
                'Мин_стоимость': min_cost,
                'Макс_стоимость': max_cost,
                'Средняя_стоимость': avg_cost
            })
    
    if all_rows:
        fieldnames = ['Источник', 'Комнатность', 'Этаж', 'Вид', 
                     'Площадь_диапазон', 'Количество_квартир', 
                     'Мин_стоимость', 'Макс_стоимость', 'Средняя_стоимость']
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        
        print(f"✓ Сводка групп сохранена в файл: {output_path}")


def print_groups(groups, source_name):
    """Выводит сгруппированные квартиры"""
    print(f"\n{'='*80}")
    print(f"ГРУППЫ ДЛЯ: {source_name}")
    print(f"{'='*80}\n")
    
    # Сортируем группы для красивого вывода
    def sort_key(group_item):
        комнатность, этаж, вид, площадь = group_item[0]
        # Извлекаем нижнюю границу площади для сортировки
        area_lower = int(площадь.split('-')[0]) if '-' in площадь else 0
        return (комнатность, этаж, вид, area_lower)
    
    sorted_groups = sorted(groups.items(), key=sort_key)
    
    for group_key, apartments in sorted_groups:
        комнатность, этаж, вид, площадь = group_key
        floor_range = get_floor_range(apartments)
        
        print(f"Группа: {комнатность}, {этаж} этаж (конкретные этажи: {floor_range}), {вид}, {площадь} м²")
        print(f"Количество квартир: {len(apartments)}")
        print("-" * 80)
        
        for apt in apartments:
            print(f"  Этаж: {apt['Этаж']}, Комнатность: {apt['Комнатность']}, "
                  f"Вид: {apt['Вид из окон']}, Площадь: {apt['Площадь']} м², "
                  f"Стоимость: {apt['Стоимость']:,} руб.")
        
        print()


def main():
    """Основная функция"""
    base_path = Path("/Users/annarybkina/Desktop/Allio/ИИ Цены")
    
    # Основной ЖК
    main_file = base_path / "Мой ЖК.csv"
    
    # Конкуренты
    competitor_files = [
        base_path / "Конкурент Вдохновение.csv",
        base_path / "Конкурент Ривьера.csv"
    ]
    
    # Словарь для хранения всех групп по источникам
    all_groups_dict = {}
    
    # Обрабатываем основной ЖК
    if main_file.exists():
        print("Обработка основного ЖК: Мой ЖК")
        apartments_main = load_and_normalize_csv(main_file)
        groups_main = group_apartments(apartments_main, "Мой ЖК")
        print_groups(groups_main, "Мой ЖК (основной ЖК)")
        all_groups_dict["Мой ЖК"] = groups_main
    else:
        print(f"Файл не найден: {main_file}")
    
    # Обрабатываем конкурентов (объединяем всех в одну группу)
    all_competitor_groups = defaultdict(list)
    
    for comp_file in competitor_files:
        if comp_file.exists():
            comp_name = comp_file.stem
            print(f"\nОбработка конкурента: {comp_name}")
            apartments_comp = load_and_normalize_csv(comp_file)
            
            # Объединяем группы конкурентов (не сохраняем отдельно)
            for apt in apartments_comp:
                group_key = (
                    apt['Комнатность_норм'],
                    apt['Этаж_норм'],
                    apt['Вид_норм'],
                    apt['Площадь_норм']
                )
                all_competitor_groups[group_key].append({
                    'Этаж': apt['Этаж'],
                    'Комнатность': apt['Комнатность'],
                    'Вид из окон': apt['Вид из окон'],
                    'Площадь': apt['Площадь'],
                    'Стоимость': apt['Стоимость_норм'],
                    'Источник': comp_name
                })
        else:
            print(f"Файл не найден: {comp_file}")
    
    # Выводим объединенные группы конкурентов
    if all_competitor_groups:
        # Сортируем квартиры в объединенных группах
        for group_key in all_competitor_groups:
            all_competitor_groups[group_key].sort(key=lambda x: x['Стоимость'])
        
        print_groups(all_competitor_groups, "Все конкуренты (объединено)")
        all_groups_dict["Все конкуренты"] = all_competitor_groups
    
    # Сохраняем один файл со сводкой всех групп
    if all_groups_dict:
        output_file = base_path / "Группы_сводка.csv"
        save_groups_summary_to_csv(all_groups_dict, output_file)


if __name__ == "__main__":
    main()
