#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для статистического анализа группы квартир
"""

import csv
import re
from pathlib import Path
import statistics

# Попытка импортировать matplotlib
try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Внимание: matplotlib не установлен. График не будет построен.")
    print("Для установки выполните: pip install matplotlib numpy")

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

def analyze_group(apartments):
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
    
    # Для графика
    if MATPLOTLIB_AVAILABLE:
        costs_array = np.array(costs)
    else:
        costs_array = None
    
    print("=" * 80)
    print("СТАТИСТИЧЕСКИЙ АНАЛИЗ ГРУППЫ")
    print("=" * 80)
    print(f"Количество квартир: {len(apartments)}")
    print(f"\nОсновные показатели:")
    print(f"  Среднее значение: {mean:,.0f} руб.")
    print(f"  Медиана: {median:,.0f} руб.")
    print(f"  Стандартное отклонение: {std:,.0f} руб.")
    print(f"\nКвартили:")
    print(f"  Q1 (25%): {q1:,.0f} руб.")
    print(f"  Q2 (медиана, 50%): {median:,.0f} руб.")
    print(f"  Q3 (75%): {q3:,.0f} руб.")
    print(f"  IQR (межквартильный размах): {iqr:,.0f} руб.")
    print(f"\nГраницы для выбросов:")
    print(f"  Нижняя граница: {lower_bound:,.0f} руб.")
    print(f"  Верхняя граница: {upper_bound:,.0f} руб.")
    print(f"\nВыбросы:")
    if outliers:
        print(f"  Количество выбросов: {len(outliers)}")
        print(f"  Минимальный выброс: {min(outliers):,.0f} руб.")
        print(f"  Максимальный выброс: {max(outliers):,.0f} руб.")
        print(f"  Значения выбросов: {sorted(outliers)}")
    else:
        print(f"  Выбросов не обнаружено")
    
    print(f"\nМинимум: {min(costs):,.0f} руб.")
    print(f"Максимум: {max(costs):,.0f} руб.")
    print("=" * 80)
    
    return costs_array, mean, median, outliers, q1, q3

def plot_boxplot(costs_array, mean, median, outliers, output_path):
    """Строит boxplot"""
    if not MATPLOTLIB_AVAILABLE or costs_array is None:
        print("\nГрафик не может быть построен: matplotlib не установлен")
        return
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Создаем boxplot
    bp = ax.boxplot(costs_array, vert=True, patch_artist=True,
                    showmeans=True, meanline=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    meanprops=dict(color='green', linewidth=2, linestyle='--'),
                    whiskerprops=dict(color='black', linewidth=1.5),
                    capprops=dict(color='black', linewidth=1.5))
    
    # Добавляем точки выбросов
    if outliers:
        outlier_x = [1] * len(outliers)
        ax.scatter(outlier_x, outliers, color='orange', s=100, alpha=0.6, 
                  zorder=3, label=f'Выбросы ({len(outliers)})')
    
    # Настройка осей
    ax.set_ylabel('Стоимость, руб.', fontsize=12, fontweight='bold')
    ax.set_title('Распределение стоимости квартир в группе\n'
                'Все конкуренты, 2к, не первый этаж, во двор, 60-70 м²',
                fontsize=14, fontweight='bold', pad=20)
    
    # Форматирование оси Y
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    # Добавляем легенду
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='red', linewidth=2, label='Медиана'),
        Line2D([0], [0], color='green', linewidth=2, linestyle='--', label='Среднее'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
               markersize=10, label=f'Выбросы ({len(outliers)})' if outliers else 'Выбросы (0)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # Добавляем сетку
    ax.grid(True, alpha=0.3, axis='y')
    
    # Добавляем текстовую информацию
    textstr = f'Среднее: {mean:,.0f} руб.\nМедиана: {median:,.0f} руб.'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nГрафик сохранен: {output_path}")
    plt.close()

def main():
    base_path = Path("/Users/annarybkina/Desktop/Allio/ИИ Цены")
    
    # Целевая группа из строки 15
    target_group = {
        'Комнатность': '2к',
        'Этаж': 'не первый',
        'Вид': 'во двор',
        'Площадь': '60-70'
    }
    
    # Файлы конкурентов
    competitor_files = [
        base_path / "Конкурент Вдохновение.csv",
        base_path / "Конкурент Ривьера.csv"
    ]
    
    print("Загрузка данных...")
    apartments = load_and_filter_apartments(competitor_files, target_group)
    
    if not apartments:
        print("Квартиры не найдены!")
        return
    
    print(f"Найдено квартир: {len(apartments)}")
    
    # Анализ
    result = analyze_group(apartments)
    costs_array = result[0]
    mean = result[1]
    median = result[2]
    outliers = result[3]
    
    # Построение графика
    if MATPLOTLIB_AVAILABLE:
        output_path = base_path / "boxplot_группа_15.png"
        plot_boxplot(costs_array, mean, median, outliers, output_path)
    
    print("\nАнализ завершен!")

if __name__ == "__main__":
    main()

