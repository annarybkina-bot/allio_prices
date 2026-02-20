#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сравнения двух групп квартир
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
    print("Внимание: matplotlib не установлен. График не будет построен.")

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
                        
                        # Проверяем, соответствует ли квартира целевой группе
                        if (rooms_norm == target_group['Комнатность'] and
                            floor_norm == target_group['Этаж'] and
                            view_norm == target_group['Вид'] and
                            area_norm == target_group['Площадь']):
                            apartments.append({
                                'Стоимость': price_norm,
                                'Этаж': row.get('Этаж', ''),
                                'Площадь': row.get('Общая площадь (м.кв.)', ''),
                                'Источник': file_path.stem
                            })
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Ошибка при чтении файла {file_path}: {e}")
                break
    
    return apartments

def analyze_group(apartments, group_name):
    """Проводит статистический анализ группы"""
    costs = sorted([apt['Стоимость'] for apt in apartments])
    
    # Основная статистика
    mean = statistics.mean(costs)
    median = statistics.median(costs)
    std = statistics.stdev(costs) if len(costs) > 1 else 0
    
    # Квартили
    q1 = statistics.quantiles(costs, n=4)[0]
    q3 = statistics.quantiles(costs, n=4)[2]
    iqr = q3 - q1
    
    # Выбросы (по правилу 1.5 * IQR)
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = [c for c in costs if c < lower_bound or c > upper_bound]
    
    print("=" * 80)
    print(f"СТАТИСТИЧЕСКИЙ АНАЛИЗ: {group_name}")
    print("=" * 80)
    print(f"Количество квартир: {len(apartments)}")
    print(f"Среднее значение: {mean:,.0f} руб.")
    print(f"Медиана: {median:,.0f} руб.")
    print(f"Стандартное отклонение: {std:,.0f} руб.")
    print(f"Q1: {q1:,.0f} руб. | Q3: {q3:,.0f} руб. | IQR: {iqr:,.0f} руб.")
    print(f"Выбросы: {len(outliers)} ({len(outliers)/len(costs)*100:.1f}%)")
    print(f"Минимум: {min(costs):,.0f} руб. | Максимум: {max(costs):,.0f} руб.")
    print("=" * 80)
    print()
    
    # Для графика
    if MATPLOTLIB_AVAILABLE:
        costs_array = np.array(costs)
    else:
        costs_array = None
    
    return costs_array, mean, median, outliers, q1, q3, std

def plot_comparison_boxplot(data1, stats1, label1, data2, stats2, label2, output_path):
    """Строит два boxplot на одном графике для сравнения"""
    if not MATPLOTLIB_AVAILABLE or data1 is None or data2 is None:
        print("\nГрафик не может быть построен: matplotlib не установлен")
        return
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Подготовка данных для boxplot
    positions = [1, 2]
    data = [data1, data2]
    
    # Создаем boxplot
    bp = ax.boxplot(data, positions=positions, widths=0.6, vert=True, patch_artist=True,
                    showmeans=True, meanline=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    meanprops=dict(color='green', linewidth=2, linestyle='--'),
                    whiskerprops=dict(color='black', linewidth=1.5),
                    capprops=dict(color='black', linewidth=1.5))
    
    # Разные цвета для коробок
    colors = ['lightblue', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Добавляем точки выбросов
    outliers1 = stats1[3]
    outliers2 = stats2[3]
    
    if outliers1:
        ax.scatter([1] * len(outliers1), outliers1, color='orange', s=100, 
                  alpha=0.6, zorder=3, marker='o')
    if outliers2:
        ax.scatter([2] * len(outliers2), outliers2, color='orange', s=100, 
                  alpha=0.6, zorder=3, marker='o')
    
    # Настройка осей
    ax.set_ylabel('Стоимость, руб.', fontsize=12, fontweight='bold')
    ax.set_xticks(positions)
    ax.set_xticklabels([label1, label2], fontsize=11, fontweight='bold')
    ax.set_title('Сравнение распределения стоимости квартир\n'
                f'{label1} vs {label2}',
                fontsize=14, fontweight='bold', pad=20)
    
    # Форматирование оси Y
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    # Добавляем легенду
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='red', linewidth=2, label='Медиана'),
        Line2D([0], [0], color='green', linewidth=2, linestyle='--', label='Среднее'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
               markersize=10, label='Выбросы')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # Добавляем сетку
    ax.grid(True, alpha=0.3, axis='y')
    
    # Добавляем текстовую информацию
    textstr1 = f'{label1}\nСреднее: {stats1[1]:,.0f} руб.\nМедиана: {stats1[2]:,.0f} руб.\nВыбросы: {len(outliers1)}'
    textstr2 = f'{label2}\nСреднее: {stats2[1]:,.0f} руб.\nМедиана: {stats2[2]:,.0f} руб.\nВыбросы: {len(outliers2)}'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
    ax.text(0.02, 0.98, textstr1, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props)
    ax.text(0.02, 0.70, textstr2, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props)
    
    # Добавляем сравнение
    diff_mean = ((stats2[1] - stats1[1]) / stats1[1]) * 100
    diff_median = ((stats2[2] - stats1[2]) / stats1[2]) * 100
    comparison_text = f'Разница:\nСреднее: {diff_mean:+.1f}%\nМедиана: {diff_median:+.1f}%'
    ax.text(0.98, 0.98, comparison_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='right', bbox=props)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"График сохранен: {output_path}")
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
    apartments5 = load_and_filter_apartments(group5_files, group5)
    print(f"Найдено квартир: {len(apartments5)}\n")
    
    print("Загрузка данных группы 15...")
    apartments15 = load_and_filter_apartments(group15_files, group15)
    print(f"Найдено квартир: {len(apartments15)}\n")
    
    if not apartments5 or not apartments15:
        print("Ошибка: не удалось загрузить данные для одной из групп!")
        return
    
    # Анализ групп
    result5 = analyze_group(apartments5, group5_label)
    result15 = analyze_group(apartments15, group15_label)
    
    # Построение графика сравнения
    if MATPLOTLIB_AVAILABLE:
        output_path = base_path / "boxplot_сравнение_5_15.png"
        plot_comparison_boxplot(
            result5[0], result5, group5_label,
            result15[0], result15, group15_label,
            output_path
        )
    
    print("\nСравнение завершено!")

if __name__ == "__main__":
    main()

