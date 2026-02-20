#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для построения наложенных гистограмм двух групп
"""

import csv
import re
from pathlib import Path
import statistics

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Внимание: matplotlib не установлен.")

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
    rooms_str = re.sub(r'[^\dк]', '', rooms_str)
    match = re.search(r'(\d+)', rooms_str)
    if match:
        return f"{match.group(1)}к"
    return rooms_str

def normalize_view(view):
    """Нормализует вид из окон: во двор или на улицу"""
    if not view or str(view).strip() == '':
        return None
    view_str = str(view).strip().lower()
    if "во двор" in view_str and "на улицу" not in view_str:
        return "во двор"
    elif "на улицу" in view_str:
        return "на улицу"
    elif "во двор" in view_str:
        return "на улицу"
    else:
        return "на улицу"

def normalize_area(area):
    """Нормализует площадь и группирует с шагом 10 м²"""
    if not area or str(area).strip() == '':
        return None
    try:
        area_str = str(area).replace(',', '.')
        area_float = float(area_str)
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
        return int(float(str(price)))
    except (ValueError, TypeError):
        return None

def load_and_filter_apartments(file_paths, target_group):
    """Загружает квартиры и фильтрует по целевой группе"""
    apartments = []
    
    for file_path in file_paths:
        if not file_path.exists():
            continue
            
        encodings = ['utf-8', 'cp1251', 'windows-1251']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        floor_norm = normalize_floor(row.get('Этаж', ''))
                        rooms_norm = normalize_rooms(row.get('Комнатность', ''))
                        view_norm = normalize_view(row.get('Вид из окон', ''))
                        area_norm = normalize_area(row.get('Общая площадь (м.кв.)', ''))
                        price_norm = normalize_price(row.get('Стоимость', ''))
                        
                        if not all([floor_norm, rooms_norm, view_norm, area_norm is not None, price_norm is not None]):
                            continue
                        
                        if (rooms_norm == target_group['Комнатность'] and
                            floor_norm == target_group['Этаж'] and
                            view_norm == target_group['Вид'] and
                            area_norm == target_group['Площадь']):
                            apartments.append(price_norm)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Ошибка при чтении файла {file_path}: {e}")
                break
    
    return apartments

def plot_overlapping_histograms(data1, label1, data2, label2, output_path):
    """Строит две наложенные гистограммы"""
    if not MATPLOTLIB_AVAILABLE:
        print("\nГрафик не может быть построен: matplotlib не установлен")
        return
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Определяем общий диапазон для обеих групп
    all_data = data1 + data2
    min_val = min(all_data)
    max_val = max(all_data)
    
    # Вычисляем оптимальное количество бинов (правило Стёрджеса)
    n1 = len(data1)
    n2 = len(data2)
    n_total = n1 + n2
    
    # Используем меньше бинов для более крупного шага (в 2 раза крупнее)
    bins = 15
    
    # Строим гистограммы с прозрачностью
    n1, bins1, patches1 = ax.hist(data1, bins=bins, alpha=0.6, label=label1, 
                                   color='steelblue', edgecolor='black', linewidth=0.5)
    n2, bins2, patches2 = ax.hist(data2, bins=bins, alpha=0.6, label=label2,
                                   color='coral', edgecolor='black', linewidth=0.5)
    
    # Добавляем вертикальные линии для средних и медиан
    mean1 = statistics.mean(data1)
    median1 = statistics.median(data1)
    mean2 = statistics.mean(data2)
    median2 = statistics.median(data2)
    
    # Средние значения
    ax.axvline(mean1, color='blue', linestyle='--', linewidth=2, 
               label=f'{label1} - Среднее: {mean1:,.0f} руб.')
    ax.axvline(mean2, color='red', linestyle='--', linewidth=2,
               label=f'{label2} - Среднее: {mean2:,.0f} руб.')
    
    # Медианы
    ax.axvline(median1, color='darkblue', linestyle='-', linewidth=2,
               label=f'{label1} - Медиана: {median1:,.0f} руб.')
    ax.axvline(median2, color='darkred', linestyle='-', linewidth=2,
               label=f'{label2} - Медиана: {median2:,.0f} руб.')
    
    # Настройка осей
    ax.set_xlabel('Стоимость, руб.', fontsize=12, fontweight='bold')
    ax.set_ylabel('Количество квартир', fontsize=12, fontweight='bold')
    ax.set_title('Сравнение распределения стоимости квартир\n'
                f'{label1} vs {label2}',
                fontsize=14, fontweight='bold', pad=20)
    
    # Форматирование оси X
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}М'))
    
    # Добавляем сетку
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_axisbelow(True)
    
    # Легенда
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    
    # Добавляем текстовую информацию
    stats_text = (
        f'{label1}:\n'
        f'  Количество: {len(data1)}\n'
        f'  Среднее: {mean1:,.0f} руб.\n'
        f'  Медиана: {median1:,.0f} руб.\n'
        f'  Ст.отклонение: {statistics.stdev(data1):,.0f} руб.\n\n'
        f'{label2}:\n'
        f'  Количество: {len(data2)}\n'
        f'  Среднее: {mean2:,.0f} руб.\n'
        f'  Медиана: {median2:,.0f} руб.\n'
        f'  Ст.отклонение: {statistics.stdev(data2):,.0f} руб.\n\n'
        f'Разница:\n'
        f'  Среднее: {((mean2-mean1)/mean1*100):+.1f}%\n'
        f'  Медиана: {((median2-median1)/median1*100):+.1f}%'
    )
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props, family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Гистограммы сохранены: {output_path}")
    plt.close()

def main():
    base_path = Path("/Users/annarybkina/Desktop/Allio/ИИ Цены")
    
    # Группа 5: Мой ЖК, 2к, не первый, на улицу, 50-60 м²
    group5 = {
        'Комнатность': '2к',
        'Этаж': 'не первый',
        'Вид': 'на улицу',
        'Площадь': '50-60'
    }
    group5_files = [base_path / "Мой ЖК.csv"]
    group5_label = "Мой ЖК: 2к, на улицу, 50-60 м²"
    
    # Группа 15: Все конкуренты, 2к, не первый, во двор, 60-70 м²
    group15 = {
        'Комнатность': '2к',
        'Этаж': 'не первый',
        'Вид': 'во двор',
        'Площадь': '60-70'
    }
    group15_files = [
        base_path / "Конкурент Вдохновение.csv",
        base_path / "Конкурент Ривьера.csv"
    ]
    group15_label = "Конкуренты: 2к, во двор, 60-70 м²"
    
    print("Загрузка данных группы 5...")
    data5 = load_and_filter_apartments(group5_files, group5)
    print(f"Найдено квартир: {len(data5)}\n")
    
    print("Загрузка данных группы 15...")
    data15 = load_and_filter_apartments(group15_files, group15)
    print(f"Найдено квартир: {len(data15)}\n")
    
    if not data5 or not data15:
        print("Ошибка: не удалось загрузить данные для одной из групп!")
        return
    
    # Построение наложенных гистограмм
    if MATPLOTLIB_AVAILABLE:
        output_path = base_path / "histogram_сравнение_5_15.png"
        plot_overlapping_histograms(data5, group5_label, data15, group15_label, output_path)
    
    print("\nСравнение завершено!")

if __name__ == "__main__":
    main()

