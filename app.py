#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask приложение для анализа и группировки квартир
"""

from flask import Flask, render_template, request, jsonify, url_for, Blueprint
import csv
import re
import os
import statistics
from pathlib import Path
from collections import defaultdict
import base64
import io

# Для Render: matplotlib должен писать кэш во временную папку
if 'MPLCONFIGDIR' not in os.environ:
    os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

try:
    import matplotlib
    matplotlib.use('Agg')  # Backend без GUI (для сервера)
    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

app = Flask(__name__, static_folder='static', static_url_path='/static')
# Секрет для сессий (на Render задайте SECRET_KEY в Environment)
app.config['SECRET_KEY'] = __import__('os').environ.get('SECRET_KEY', 'dev-secret-change-in-production')

# Создаем Blueprint для Аквилона
akvilon_bp = Blueprint('akvilon', __name__, url_prefix='/akvilon')

# Функции нормализации (из apartment_analyzer.py)
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
    
    rooms_str = re.sub(r'[^\dк]', '', rooms_str)
    match = re.search(r'(\d+)', rooms_str)
    if match:
        return f"{match.group(1)}к"
    return rooms_str

def normalize_view(view):
    """Нормализует вид из окон: во двор или на улицу"""
    if not view or str(view).strip() == '':
        # Если поле пустое, используем значение по умолчанию "на улицу"
        return "на улицу"
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
        # Убираем все пробелы (разделители тысяч), символы валют и другие нечисловые символы, кроме точки и запятой
        price_str = str(price).strip()
        # Убираем символы валют (₽, руб, руб., и т.д.)
        price_str = price_str.replace('₽', '').replace('руб', '').replace('руб.', '').replace('RUB', '')
        # Убираем все пробелы и неразрывные пробелы
        price_str = price_str.replace(' ', '').replace('\xa0', '').replace('\u2009', '')  # \xa0 - неразрывный пробел, \u2009 - тонкий пробел
        # Заменяем запятую на точку для парсинга
        price_str = price_str.replace(',', '.')
        # Убираем все оставшиеся нечисловые символы кроме точки и минуса
        price_str = ''.join(c for c in price_str if c.isdigit() or c in '.-')
        if not price_str or price_str in ['.', '-']:
            return None
        return int(float(price_str))
    except (ValueError, TypeError):
        return None

def normalize_area_type(area_type):
    """Нормализует тип площади к единому формату"""
    if not area_type:
        return None
    
    area_type_str = str(area_type).strip()
    area_type_lower = area_type_str.lower()
    
    # Нормализуем пробелы
    area_type_lower = ' '.join(area_type_lower.split())
    area_type_lower_no_spaces = area_type_lower.replace(' ', '')
    
    # 1. Студии -> "XS (Студия)"
    if 'студи' in area_type_lower or area_type_lower == 'xs' or area_type_lower.startswith('xs'):
        return 'XS (Студия)'
    
    # Исправляем опечатки: "З" (кириллическая) вместо "3" в "3Евро"
    area_type_lower = area_type_lower.replace('зевро', '3евро').replace('зеuro', '3евро')
    area_type_lower_no_spaces = area_type_lower.replace(' ', '')
    
    # 2. Евро-планировки (S, M, L) - только для 2, 3, 4 комнат
    # Сначала проверяем форматы типа "2ккв (Евро)", "3ккв (Евро)", "4ккв (Евро)"
    match_euro = re.search(r'(\d+)\s*[кkкквkv].*евро', area_type_lower)
    if match_euro:
        room_count = int(match_euro.group(1))
        if room_count == 2:
            return 'S (2Евро)'
        elif room_count == 3:
            return 'M (3Евро)'
        elif room_count == 4:
            return 'L (4Евро)'
        # Для 5+ комнат с упоминанием евро - игнорируем "евро", это обычная квартира
        elif room_count >= 5:
            return f"{room_count}к"
    
    # S (2Евро) - 2 комнаты евро
    if (area_type_lower.startswith('s') and 'евро' in area_type_lower) or '2евро' in area_type_lower_no_spaces:
        return 'S (2Евро)'
    
    # M (3Евро) - 3 комнаты евро
    # Если просто "M" или "M " (без цифр и без "к"), это евро-планировка
    if area_type_lower.startswith('m'):
        # Проверяем, что это не "м2" или что-то подобное
        if len(area_type_lower) <= 2 or (not re.search(r'\d', area_type_lower) and 'к' not in area_type_lower):
            return 'M (3Евро)'
        # Или если есть упоминание евро
        if 'евро' in area_type_lower or '3евро' in area_type_lower_no_spaces:
            return 'M (3Евро)'
    
    # L (4Евро) - 4 комнаты евро
    # Если просто "L" или "L " (без цифр и без "к"), это евро-планировка
    if area_type_lower.startswith('l'):
        # Проверяем, что это не "л2" или что-то подобное
        if len(area_type_lower) <= 2 or (not re.search(r'\d', area_type_lower) and 'к' not in area_type_lower):
            return 'L (4Евро)'
        # Или если есть упоминание евро
        if 'евро' in area_type_lower or '4евро' in area_type_lower_no_spaces:
            return 'L (4Евро)'
    
    # 3. Обычные квартиры (1к, 2к, 3к, 4к, 5к, 6к и т.д.)
    # Ищем паттерны: "1к", "1 к", "1ккв", "1 ккв", "1K", "1 K", "5ккв", "5 ккв" и т.д.
    # Для 5+ комнат игнорируем упоминание "евро" - это всегда обычная квартира
    match = re.search(r'(\d+)\s*[кkкквkv]', area_type_lower)
    if match:
        room_count = int(match.group(1))
        # Возвращаем с кириллической "к"
        return f"{room_count}к"
    
    # Если ничего не подошло, возвращаем оригинал с нормализованными пробелами
    return area_type_str

def load_csv_from_string(csv_content, filename=''):
    """Загружает CSV из строки с новым форматом"""
    apartments = []
    required_fields = ['Название объекта', 'Тип площади', 'Площадь общая', 'Стоимость']
    missing_fields = []
    
    try:
        # Используем более гибкий парсер CSV с поддержкой многострочных полей
        reader = csv.DictReader(io.StringIO(csv_content), quoting=csv.QUOTE_MINIMAL)
        # Нормализуем названия колонок (убираем пробелы в начале и конце, невидимые символы, переносы строк)
        original_fieldnames = reader.fieldnames if reader.fieldnames else []
        # Сохраняем оригинальные названия, но также создаем нормализованные версии для поиска
        # Убираем переносы строк внутри названий полей (могут быть из-за многострочных CSV)
        fieldnames = []
        for f in original_fieldnames:
            if f:
                # Убираем переносы строк, невидимые символы, нормализуем пробелы
                normalized = f.replace('\n', ' ').replace('\r', ' ').replace('\ufeff', '').replace('\u200b', '')
                normalized = ' '.join(normalized.split())  # Убираем множественные пробелы
                fieldnames.append(normalized.strip())
            else:
                fieldnames.append('')
        
        # Создаем маппинг нормализованных названий к оригинальным
        field_mapping = {}
        for orig, norm in zip(original_fieldnames, fieldnames):
            field_mapping[norm] = orig
        
        # Проверяем наличие всех обязательных полей (с учетом возможных вариаций)
        found_fields = {}  # required_field -> оригинальное название из файла
        for required_field in required_fields:
            found = False
            # Нормализуем требуемое поле: убираем все пробелы и переносы строк
            normalized_required = required_field.strip().replace('\n', ' ').replace('\r', ' ')
            normalized_required = ''.join(normalized_required.split()).lower()
            
            for i, field in enumerate(fieldnames):
                if not field:
                    continue
                # Нормализуем поле для сравнения: убираем все пробелы, переносы строк, невидимые символы
                normalized_field = field.strip().replace('\n', ' ').replace('\r', ' ')
                normalized_field = normalized_field.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', ' ')
                normalized_field = ''.join(normalized_field.split()).lower()  # Убираем все пробелы
                
                # Сравниваем нормализованные версии
                if normalized_field == normalized_required:
                    found_fields[required_field] = original_fieldnames[i]  # Сохраняем оригинальное название
                    found = True
                    break
            if not found:
                missing_fields.append(required_field)
        
        if missing_fields:
            # Показываем доступные поля для отладки
            available_fields = ', '.join(fieldnames) if fieldnames else 'нет полей'
            # Также показываем оригинальные названия для отладки
            original_fields = ', '.join([f for f in original_fieldnames if f]) if original_fieldnames else 'нет полей'
            # Показываем найденные поля
            found_fields_str = ', '.join([f"{k} -> {v}" for k, v in found_fields.items()])
            error_msg = f"В файле '{filename}' отсутствуют обязательные поля: {', '.join(missing_fields)}. Найдены поля (нормализованные): {available_fields}. Оригинальные поля: {original_fields}. Маппинг найденных: {found_fields_str}"
            raise ValueError(error_msg)
        
        # Проверяем, что все обязательные поля найдены
        if len(found_fields) != len(required_fields):
            missing = [f for f in required_fields if f not in found_fields]
            error_msg = f"В файле '{filename}' не все обязательные поля найдены. Отсутствуют: {', '.join(missing)}"
            raise ValueError(error_msg)

        # Подготовим поиск дополнительных полей по нормализованным названиям,
        # чтобы учитывать возможные пробелы/регистр.
        extra_field_names = ['Застройщик', 'Район', 'Класс', 'Этажность', 'Срок сдачи', 'Тип дома', 'Отделка']
        extra_field_mapping = {}  # extra_name -> (orig_key, norm_key)
        for extra_name in extra_field_names:
            # Базовое нормализованное имя (без пробелов и регистра)
            normalized_required = ''.join(extra_name.strip().split()).lower()
            # Для некоторых полей поддерживаем альтернативные названия колонок
            # Например, "Этажность" в файлах может называться "Этажей"
            alternative_required = None
            if extra_name == 'Этажность':
                alternative_required = 'этажей'
            orig_key = None
            norm_key = None
            for i, field in enumerate(fieldnames):
                if not field:
                    continue
                normalized_field = field.strip().replace('\n', ' ').replace('\r', ' ')
                normalized_field = normalized_field.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', ' ')
                normalized_field_comp = ''.join(normalized_field.split()).lower()
                if (normalized_field_comp == normalized_required or
                    (alternative_required is not None and normalized_field_comp == alternative_required)):
                    orig_key = original_fieldnames[i]
                    norm_key = field.strip()
                    break
            if orig_key:
                extra_field_mapping[extra_name] = (orig_key, norm_key)
        
        for row_num, row in enumerate(reader, start=2):  # start=2, т.к. первая строка - заголовки
            # Нормализуем ключи строки (убираем переносы строк из названий полей)
            normalized_row = {}
            for key, value in row.items():
                if key:
                    # Нормализуем ключ так же, как мы нормализовали fieldnames
                    normalized_key = key.replace('\n', ' ').replace('\r', ' ').replace('\ufeff', '').replace('\u200b', '')
                    normalized_key = ' '.join(normalized_key.split()).strip()
                    normalized_row[normalized_key] = value
            
            # Извлекаем обязательные поля, используя найденные названия
            object_name_key = found_fields.get('Название объекта', 'Название объекта')
            area_type_key = found_fields.get('Тип площади', 'Тип площади')
            total_area_key = found_fields.get('Площадь общая', 'Площадь общая')
            price_key = found_fields.get('Стоимость', 'Стоимость')
            
            # Нормализуем ключи для поиска в normalized_row
            object_name_norm = object_name_key.replace('\n', ' ').replace('\r', ' ').replace('\ufeff', '').replace('\u200b', '')
            object_name_norm = ' '.join(object_name_norm.split()).strip()
            area_type_norm = area_type_key.replace('\n', ' ').replace('\r', ' ').replace('\ufeff', '').replace('\u200b', '')
            area_type_norm = ' '.join(area_type_norm.split()).strip()
            total_area_norm = total_area_key.replace('\n', ' ').replace('\r', ' ').replace('\ufeff', '').replace('\u200b', '')
            total_area_norm = ' '.join(total_area_norm.split()).strip()
            price_norm = price_key.replace('\n', ' ').replace('\r', ' ').replace('\ufeff', '').replace('\u200b', '')
            price_norm = ' '.join(price_norm.split()).strip()
            
            # Пробуем найти поля разными способами
            object_name = ''
            area_type = ''
            total_area = ''
            price_str = ''
            
            # Ищем по нормализованному ключу
            if object_name_norm in normalized_row:
                object_name = str(normalized_row[object_name_norm]).strip()
            # Если не нашли, пробуем найти в оригинальной строке
            elif object_name_key in row:
                object_name = str(row[object_name_key]).strip()
            
            if area_type_norm in normalized_row:
                area_type = str(normalized_row[area_type_norm]).strip()
            elif area_type_key in row:
                area_type = str(row[area_type_key]).strip()
            
            if total_area_norm in normalized_row:
                total_area = str(normalized_row[total_area_norm]).strip()
            elif total_area_key in row:
                total_area = str(row[total_area_key]).strip()
            
            # Убираем переносы строк из значений
            object_name = object_name.replace('\n', ' ').replace('\r', ' ').strip()
            area_type = area_type.replace('\n', ' ').replace('\r', ' ').strip()
            total_area = total_area.replace('\n', ' ').replace('\r', ' ').strip()
            
            # Для ЖК "Залив 1" и "Аквилон ZaLive" используем столбец "100% стоимость" вместо "Стоимость"
            use_100_percent_price = False
            if object_name and (('залив' in object_name.lower() and '1' in object_name) or 
                               'аквилон' in object_name.lower()):
                use_100_percent_price = True
                # Ищем столбец "100% стоимость" или его варианты
                price_100_key = None
                price_100_norm = None
                for field in fieldnames:
                    if field:
                        normalized_field = field.strip().replace('\n', ' ').replace('\r', ' ')
                        normalized_field = normalized_field.replace('\ufeff', '').replace('\u200b', '')
                        normalized_field_lower = ''.join(normalized_field.split()).lower()
                        # Ищем варианты: "100%стоимость", "100% стоимость", "стоимостьпри100%" и т.д.
                        if '100' in normalized_field_lower and ('стоимость' in normalized_field_lower or 'cost' in normalized_field_lower):
                            # Находим оригинальное название поля
                            for orig_field in original_fieldnames:
                                if orig_field and field.strip() == orig_field.strip():
                                    price_100_key = orig_field
                                    price_100_norm = normalized_field.strip()
                                    break
                            if price_100_key:
                                break
                
                if price_100_key:
                    # Используем столбец "100% стоимость"
                    if price_100_norm in normalized_row:
                        price_str = str(normalized_row[price_100_norm]).strip()
                    elif price_100_key in row:
                        price_str = str(row[price_100_key]).strip()
            
            # Если не нашли "100% стоимость" или это не "Залив 1"/"Аквилон", используем обычный столбец "Стоимость"
            if not use_100_percent_price or not price_str:
                if price_norm in normalized_row:
                    price_str = str(normalized_row[price_norm]).strip()
                elif price_key in row:
                    price_str = str(row[price_key]).strip()
            
            # Отладочная информация для Аквилон
            if use_100_percent_price and not price_str:
                print(f"Предупреждение: для {object_name} не найден столбец '100% стоимость', используем обычный 'Стоимость'")
            
            # Убираем переносы строк из стоимости
            price_str = price_str.replace('\n', ' ').replace('\r', ' ').strip()
            
            # Валидация полей
            if not object_name:
                print(f"Предупреждение: строка {row_num} - пустое поле 'Название объекта', пропускаем")
                continue
            
            if not area_type:
                print(f"Предупреждение: строка {row_num} - пустое поле 'Тип площади', пропускаем")
                continue
            
            # Нормализуем тип площади к единому формату
            area_type = normalize_area_type(area_type)
            if not area_type:
                print(f"Предупреждение: строка {row_num} - не удалось нормализовать 'Тип площади', пропускаем")
                continue
            
            if not total_area:
                print(f"Предупреждение: строка {row_num} - пустое поле 'Площадь общая', пропускаем")
                continue
            
            # Нормализуем площадь - убираем единицы измерения и лишние символы
            try:
                # Убираем "м²", пробелы и другие символы, оставляем только число
                area_clean = str(total_area).replace('м²', '').replace('м2', '').replace(' ', '').replace('\xa0', '')
                area_float = float(area_clean.replace(',', '.'))
            except (ValueError, TypeError) as e:
                print(f"Предупреждение: строка {row_num} - неверный формат 'Площадь общая': '{total_area}', ошибка: {e}, пропускаем")
                continue
            
            # Нормализуем стоимость
            price_norm = normalize_price(price_str)
            if price_norm is None:
                print(f"Предупреждение: строка {row_num} - неверный формат 'Стоимость': '{price_str}', пропускаем")
                continue
            
            # Дополнительные характеристики (если есть в файле)
            extra_fields = {}
            for extra_name in extra_field_names:
                mapping = extra_field_mapping.get(extra_name)
                if not mapping:
                    continue
                orig_extra_key, norm_extra_key = mapping

                val = ''
                # Сначала пробуем по нормализованному ключу
                if norm_extra_key in normalized_row:
                    val = normalized_row.get(norm_extra_key, '')
                elif orig_extra_key in row:
                    val = row.get(orig_extra_key, '')

                if val is None:
                    val = ''
                val = str(val).strip()
                if val != '':
                    extra_fields[extra_name] = val

            apt_record = {
                'Название объекта': object_name,
                'Тип площади': area_type,
                'Площадь общая': area_float,
                'Стоимость': price_norm
            }
            # Добавляем характеристики только если они непустые
            apt_record.update(extra_fields)

            apartments.append(apt_record)
            
    except ValueError as e:
        # Пробрасываем ошибки валидации наверх
        raise e
    except Exception as e:
        error_msg = f"Ошибка при загрузке CSV файла '{filename}': {str(e)}"
        raise ValueError(error_msg)
    
    return apartments

def group_apartments(apartments, source_name):
    """Группирует квартиры по типу площади"""
    groups = defaultdict(list)
    object_names = set()  # Собираем уникальные названия объектов
    
    for apt in apartments:
        # Группируем только по типу площади
        group_key = apt['Тип площади']
        object_names.add(apt['Название объекта'])
        
        groups[group_key].append({
            'Название объекта': apt['Название объекта'],
            'Площадь общая': apt['Площадь общая'],
            'Стоимость': apt['Стоимость']
        })
    
    # Сортируем квартиры по стоимости внутри каждой группы
    for group_key in groups:
        groups[group_key].sort(key=lambda x: x['Стоимость'])
    
    # Возвращаем также название объекта (берем первое уникальное)
    object_name = list(object_names)[0] if object_names else source_name
    
    return groups, object_name

def calculate_statistics(costs):
    """Вычисляет статистику для группы"""
    if not costs:
        return None
    
    costs_sorted = sorted(costs)
    mean = statistics.mean(costs_sorted)
    median = statistics.median(costs_sorted)
    std = statistics.stdev(costs_sorted) if len(costs_sorted) > 1 else 0
    q1 = statistics.quantiles(costs_sorted, n=4)[0]
    q3 = statistics.quantiles(costs_sorted, n=4)[2]
    iqr = q3 - q1
    
    # Выбросы
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers_lower = [c for c in costs_sorted if c < lower_bound]
    outliers_upper = [c for c in costs_sorted if c > upper_bound]
    outliers_all = outliers_lower + outliers_upper
    
    return {
        'mean': mean,
        'median': median,
        'std': std,
        'min': min(costs_sorted),
        'max': max(costs_sorted),
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'outliers': outliers_all,
        'outliers_lower': outliers_lower,
        'outliers_upper': outliers_upper,
        'outliers_count': len(outliers_all),
        'outliers_lower_count': len(outliers_lower),
        'outliers_upper_count': len(outliers_upper)
    }

def plot_to_base64(fig):
    """Конвертирует matplotlib figure в base64 строку"""
    img = io.BytesIO()
    fig.savefig(img, format='png', dpi=100, bbox_inches='tight')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close(fig)
    return img_base64

@app.route('/health')
def health():
    """Проверка работы сервера (для Render и отладки)."""
    return jsonify({"status": "ok"}), 200


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prototype')
def prototype():
    """Прототип интерфейса со скриншотом и уведомлениями"""
    return render_template('prototype.html')

# Маршруты для Аквилона
@akvilon_bp.route('/')
def akvilon_index():
    return render_template('index.html')

@akvilon_bp.route('/prototype')
def akvilon_prototype():
    """Прототип интерфейса со скриншотом и уведомлениями"""
    return render_template('prototype.html')

@app.route('/api/upload_screenshot', methods=['POST'])
def upload_screenshot():
    """Загружает скриншот на сервер"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            filename = 'screenshot.png'
            filepath = Path(app.static_folder) / filename
            file.save(str(filepath))
            return jsonify({'success': True, 'url': url_for('static', filename=filename)})
        else:
            return jsonify({'error': 'Неподдерживаемый формат файла'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@akvilon_bp.route('/api/upload_screenshot', methods=['POST'])
def akvilon_upload_screenshot():
    """Загружает скриншот на сервер (Аквилон)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            filename = 'screenshot.png'
            filepath = Path(app.static_folder) / filename
            file.save(str(filepath))
            return jsonify({'success': True, 'url': url_for('static', filename=filename)})
        else:
            return jsonify({'error': 'Неподдерживаемый формат файла'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@akvilon_bp.route('/api/create_groups', methods=['POST'])
def akvilon_create_groups():
    """Создает группы из загруженных файлов (Аквилон)"""
    return create_groups_impl()

def normalize_object_name(object_name):
    """Нормализует название объекта: для Аквилон ZaLive оставляет только очередь, без корпуса"""
    if not object_name:
        return 'Неизвестный объект'
    
    # Проверяем, является ли это объектом Аквилон ZaLive
    if 'Аквилон ZaLive' in object_name:
        # Извлекаем часть до корпуса (до слова "корпус" или "корп")
        # Ищем паттерн: "Аквилон ZaLive X очередь" (до корпуса)
        match = re.search(r'(Аквилон ZaLive\s+\d+\s+очередь)', object_name, re.IGNORECASE)
        if match:
            return match.group(1)
        # Если не нашли, пытаемся найти просто "Аквилон ZaLive X очередь"
        match = re.search(r'(Аквилон\s+ZaLive\s+\d+\s+очередь)', object_name, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return object_name

def create_groups_impl():
    """Реализация создания групп (используется обоими маршрутами)"""
    try:
        main_files = request.files.getlist('main_file')
        competitor_files = request.files.getlist('competitor_files')
        
        if not main_files or len(main_files) == 0:
            return jsonify({'error': 'Не загружен файл основного ЖК'}), 400
        
        # Загружаем все файлы основного ЖК и группируем по объектам
        main_objects_data = defaultdict(list)  # название объекта -> квартиры
        
        for main_file in main_files:
            try:
                main_content = main_file.read().decode('utf-8-sig')
                main_apartments = load_csv_from_string(main_content, main_file.filename)
                # Группируем квартиры по нормализованному названию объекта
                for apt in main_apartments:
                    original_name = apt.get('Название объекта', 'Неизвестный объект')
                    object_name = normalize_object_name(original_name)
                    main_objects_data[object_name].append(apt)
            except ValueError as e:
                # Ошибки валидации полей
                return jsonify({'error': str(e)}), 400
        
        if not main_objects_data:
            return jsonify({'error': 'Не удалось загрузить данные из файлов основного ЖК. Проверьте формат файлов.'}), 400
        
        # Загружаем конкурентов и группируем по объектам
        competitor_objects_data = defaultdict(list)  # название объекта -> квартиры
        
        for comp_file in competitor_files:
            try:
                comp_content = comp_file.read().decode('utf-8-sig')
                comp_apartments = load_csv_from_string(comp_content, comp_file.filename)
                # Группируем квартиры по нормализованному названию объекта
                for apt in comp_apartments:
                    original_name = apt.get('Название объекта', 'Неизвестный объект')
                    object_name = normalize_object_name(original_name)
                    competitor_objects_data[object_name].append(apt)
            except ValueError as e:
                # Ошибки валидации полей
                return jsonify({'error': str(e)}), 400
        
        # Формируем список групп для вывода
        groups_list = []
        
        # Группы основного ЖК (группировка по объектам и типу площади)
        for object_name, apartments in main_objects_data.items():
            object_groups, _ = group_apartments(apartments, object_name)
            
            for area_type, apts in object_groups.items():
                # Извлекаем стоимости и площади
                costs = [apt['Стоимость'] for apt in apts]
                areas = [apt['Площадь общая'] for apt in apts]
                
                # Проверяем, что стоимости валидны (не None и > 0)
                costs = [c for c in costs if c is not None and c > 0]
                areas = [a for a in areas if a is not None and a > 0]
                
                if not costs or not areas:
                    print(f"Предупреждение: группа {area_type} для {object_name} не содержит валидных данных, пропускаем")
                    continue
                
                # Сортируем для правильного расчета медианы
                costs_sorted = sorted(costs)
                areas_sorted = sorted(areas)
                
                total_area = sum(areas)  # Суммарная площадь группы
                min_cost = min(costs_sorted) if costs_sorted else 0  # Минимальная стоимость
                min_area = min(areas_sorted) if areas_sorted else 0  # Минимальная площадь
                max_cost = max(costs_sorted) if costs_sorted else 0  # Максимальная стоимость
                max_area = max(areas_sorted) if areas_sorted else 0  # Максимальная площадь
                avg_cost = statistics.mean(costs_sorted) if costs_sorted else 0  # Средняя стоимость
                avg_area = statistics.mean(areas_sorted) if areas_sorted else 0  # Средняя площадь
                stats = calculate_statistics(costs_sorted)
                
                # Рассчитываем цены за квадратный метр
                price_per_sqm = [cost / area if area > 0 else 0 for cost, area in zip(costs_sorted, areas_sorted)]
                price_per_sqm = [p for p in price_per_sqm if p > 0]  # Убираем нулевые значения
                price_per_sqm_sorted = sorted(price_per_sqm) if price_per_sqm else []
                
                min_price_per_sqm = min(price_per_sqm_sorted) if price_per_sqm_sorted else 0
                max_price_per_sqm = max(price_per_sqm_sorted) if price_per_sqm_sorted else 0
                avg_price_per_sqm = statistics.mean(price_per_sqm_sorted) if price_per_sqm_sorted else 0
                
                groups_list.append({
                    'id': f"main_{len(groups_list)}",
                    'source': object_name,
                    'is_main': True,  # Флаг для основных ЖК
                    'тип_площади': area_type,
                    'количество': len(apts),
                    'общая_площадь': total_area,
                    'мин_стоимость': min_cost,
                    'мин_площадь': min_area,
                    'макс_стоимость': max_cost,
                    'макс_площадь': max_area,
                    'сред_стоимость': avg_cost,
                    'сред_площадь': avg_area,
                    'мин_цена_за_м2': min_price_per_sqm,
                    'сред_цена_за_м2': avg_price_per_sqm,
                    'макс_цена_за_м2': max_price_per_sqm,
                    'costs': costs_sorted,  # Используем отсортированные стоимости
                    'areas': areas_sorted,  # Используем отсортированные площади
                    'price_per_sqm': price_per_sqm_sorted,  # Цены за м² для графиков
                    'stats': stats
                })
        
        # Группы конкурентов (группировка по объектам и типу площади)
        for object_name, apartments in competitor_objects_data.items():
            object_groups, _ = group_apartments(apartments, object_name)
            
            for area_type, apts in object_groups.items():
                # Извлекаем стоимости и площади
                costs = [apt['Стоимость'] for apt in apts]
                areas = [apt['Площадь общая'] for apt in apts]
                
                # Проверяем, что стоимости валидны (не None и > 0)
                costs = [c for c in costs if c is not None and c > 0]
                areas = [a for a in areas if a is not None and a > 0]
                
                if not costs or not areas:
                    print(f"Предупреждение: группа {area_type} для {object_name} не содержит валидных данных, пропускаем")
                    continue
                
                # Сортируем для правильного расчета медианы
                costs_sorted = sorted(costs)
                areas_sorted = sorted(areas)
                
                total_area = sum(areas)  # Суммарная площадь группы
                min_cost = min(costs_sorted) if costs_sorted else 0  # Минимальная стоимость
                min_area = min(areas_sorted) if areas_sorted else 0  # Минимальная площадь
                max_cost = max(costs_sorted) if costs_sorted else 0  # Максимальная стоимость
                max_area = max(areas_sorted) if areas_sorted else 0  # Максимальная площадь
                avg_cost = statistics.mean(costs_sorted) if costs_sorted else 0  # Средняя стоимость
                avg_area = statistics.mean(areas_sorted) if areas_sorted else 0  # Средняя площадь
                stats = calculate_statistics(costs_sorted)
                
                # Рассчитываем цены за квадратный метр
                price_per_sqm = [cost / area if area > 0 else 0 for cost, area in zip(costs_sorted, areas_sorted)]
                price_per_sqm = [p for p in price_per_sqm if p > 0]  # Убираем нулевые значения
                price_per_sqm_sorted = sorted(price_per_sqm) if price_per_sqm else []
                
                min_price_per_sqm = min(price_per_sqm_sorted) if price_per_sqm_sorted else 0
                max_price_per_sqm = max(price_per_sqm_sorted) if price_per_sqm_sorted else 0
                avg_price_per_sqm = statistics.mean(price_per_sqm_sorted) if price_per_sqm_sorted else 0
                
                groups_list.append({
                    'id': f"comp_{len(groups_list)}",
                    'source': object_name,
                    'is_main': False,  # Флаг для конкурентов
                    'тип_площади': area_type,
                    'количество': len(apts),
                    'общая_площадь': total_area,
                    'мин_стоимость': min_cost,
                    'мин_площадь': min_area,
                    'макс_стоимость': max_cost,
                    'макс_площадь': max_area,
                    'сред_стоимость': avg_cost,
                    'сред_площадь': avg_area,
                    'мин_цена_за_м2': min_price_per_sqm,
                    'сред_цена_за_м2': avg_price_per_sqm,
                    'макс_цена_за_м2': max_price_per_sqm,
                    'costs': costs_sorted,  # Используем отсортированные стоимости
                    'areas': areas_sorted,  # Используем отсортированные площади
                    'price_per_sqm': price_per_sqm_sorted,  # Цены за м² для графиков
                    'stats': stats
                })
        
        # Создаем графики/боксплоты для всех ЖК
        boxplot_img = create_all_boxplots(groups_list) if (PLOTLY_AVAILABLE or MATPLOTLIB_AVAILABLE) else None

        # Характеристики ЖК (собираем по всем объектам, основной и конкуренты)
        characteristics = build_characteristics(main_objects_data, competitor_objects_data)
        
        return jsonify({
            'groups': groups_list,
            'boxplot': boxplot_img,
            'characteristics': characteristics
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@akvilon_bp.route('/api/compare_groups', methods=['POST'])
def akvilon_compare_groups():
    """Сравнивает сопоставимые группы (Аквилон)"""
    return compare_groups_impl()

def compare_groups_impl():
    """Реализация сравнения групп (используется обоими маршрутами)"""
    try:
        data = request.json
        groups = data.get('groups', [])
        
        # Находим сопоставимые группы (одинаковый тип площади, разные источники)
        comparable_pairs = []
        
        for i, group1 in enumerate(groups):
            for j, group2 in enumerate(groups[i+1:], start=i+1):
                # Проверяем, что тип площади одинаковый, но источники разные
                if (group1['тип_площади'] == group2['тип_площади'] and
                    group1['source'] != group2['source']):
                    
                    comparable_pairs.append({
                        'group1': group1,
                        'group2': group2
                    })
        
        if not comparable_pairs:
            return jsonify({'error': 'Не найдено сопоставимых групп'}), 400
        
        # Создаем графики для каждой пары
        comparisons = []
        
        for pair in comparable_pairs:
            g1 = pair['group1']
            g2 = pair['group2']
            
            # Определяем, какая группа - основной ЖК ("Мой ЖК")
            if g1['source'] == 'Мой ЖК':
                main_group = g1
                competitor_group = g2
            elif g2['source'] == 'Мой ЖК':
                main_group = g2
                competitor_group = g1
            else:
                # Если нет группы "Мой ЖК", используем первую как основную
                main_group = g1
                competitor_group = g2
            
            # Вычисляем процентную разницу для основных показателей
            def calculate_percentage_diff(main_val, comp_val):
                if comp_val == 0:
                    return None
                return ((main_val - comp_val) / comp_val) * 100
            
            stats1 = main_group['stats']
            stats2 = competitor_group['stats']
            
            percentage_diffs = {
                'mean': calculate_percentage_diff(stats1['mean'], stats2['mean']),
                'median': calculate_percentage_diff(stats1['median'], stats2['median']),
                'min': calculate_percentage_diff(stats1['min'], stats2['min']),
                'max': calculate_percentage_diff(stats1['max'], stats2['max'])
            }
            
            # Boxplot
            boxplot_img = create_boxplot(g1, g2) if MATPLOTLIB_AVAILABLE else None
            
            # Histogram
            histogram_img = create_histogram(g1, g2) if MATPLOTLIB_AVAILABLE else None
            
            comparisons.append({
                'group1': {
                    'source': g1['source'],
                    'stats': g1['stats']
                },
                'group2': {
                    'source': g2['source'],
                    'stats': g2['stats']
                },
                'parameters': {
                    'тип_площади': g1['тип_площади']
                },
                'percentage_diffs': percentage_diffs,
                'main_source': main_group['source'],
                'boxplot': boxplot_img,
                'histogram': histogram_img
            })
        
        return jsonify({'comparisons': comparisons})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Маршруты основного приложения, использующие общие функции
@app.route('/api/create_groups', methods=['POST'])
def create_groups():
    """Создает группы из загруженных файлов"""
    return create_groups_impl()

@app.route('/api/compare_groups', methods=['POST'])
def compare_groups():
    """Сравнивает сопоставимые группы"""
    return compare_groups_impl()

def create_all_boxplots(groups):
    """Создает интерактивные графики (Plotly) для каждого типа площадей.

    Для каждого типа площади:
    - по оси X: ЖК;
    - по левой оси Y: цена за м² (прямоугольник от Q1 до Q3, линия среднего, выбросы);
    - по правой оси Y: количество квартир (оранжевая точка).

    Возвращает словарь: тип площади -> {data, layout, div_id, title}.
    """
    if not PLOTLY_AVAILABLE:
        return None

    # Сначала собираем все уникальные ЖК из всех групп
    all_objects = {}
    for group in groups:
        object_name = group.get('source', 'Неизвестный объект')
        if object_name not in all_objects:
            all_objects[object_name] = {
                'is_main': group.get('is_main', False)
            }

    if not all_objects:
        return None

    # Группируем группы по типу площади
    area_type_map = {}
    for group in groups:
        area_type = group.get('тип_площади', 'Неизвестный тип')
        if area_type not in area_type_map:
            area_type_map[area_type] = []
        area_type_map[area_type].append(group)

    if not area_type_map:
        return None

    # Порядок типов площади для сортировки
    area_type_order = [
        'XS (Студия)',
        '1к',
        'S (2Евро)',
        '2к',
        'M (3Евро)',
        '3к',
        'L (4Евро)',
        '4к',
        '5к',
        '6к',
        '7к',
        '8к'
    ]

    # Сортируем типы площади по заданному порядку
    sorted_area_types = sorted(
        area_type_map.keys(),
        key=lambda x: area_type_order.index(x) if x in area_type_order else 999
    )

    # Сортируем ЖК: сначала основные (True), потом конкуренты
    sorted_objects = sorted(
        all_objects.items(),
        key=lambda x: (not x[1]['is_main'], x[0])
    )

    boxplots = {}

    for area_type in sorted_area_types:
        groups_for_type = area_type_map[area_type]

        # Группируем по ЖК для этого типа площади
        objects_map = {}
        for group in groups_for_type:
            object_name = group.get('source', 'Неизвестный объект')
            if object_name not in objects_map:
                objects_map[object_name] = {
                    'price_per_sqm': [],
                    'count': 0,
                    'is_main': group.get('is_main', False)
                }
            # Используем цены за м², так как задача — анализ "стоимости метра"
            if group.get('price_per_sqm'):
                objects_map[object_name]['price_per_sqm'].extend(
                    [v for v in group['price_per_sqm'] if v is not None and v > 0]
                )
            # Суммируем количество квартир для этого типа площади
            count_val = group.get('количество') or 0
            try:
                objects_map[object_name]['count'] += int(count_val)
            except (TypeError, ValueError):
                pass

        # Подготавливаем данные для графика: одна "полоса" на ЖК
        price_data = []
        labels = []
        colors = []
        counts = []

        for object_name, obj_info in sorted_objects:
            obj_data = objects_map.get(object_name)
            if not obj_data:
                continue

            # Берём только валидные значения "цена за м²"
            values = [v for v in obj_data.get('price_per_sqm', []) if v is not None and v > 0]
            if not values:
                # Для этого ЖК в данном типе нет валидных значений — пропускаем,
                # но другие ЖК для этого типа всё равно будут отображены.
                continue

            # Немного сокращаем слишком длинные названия
            short_name = object_name if len(object_name) <= 25 else object_name[:22] + '...'
            labels.append(short_name)
            price_data.append(values)
            counts.append(max(int(obj_data.get('count') or 0), 0))

            # Основной ЖК — зелёный, конкуренты — синий
            if obj_info.get('is_main', False):
                colors.append('#A5D6A7')  # светло‑зелёный
            else:
                colors.append('#90CAF9')  # светло‑синий

        if not price_data:
            # Для этого типа нет валидных данных — пропускаем
            continue

        # Цвета осей (сохраняем прежнюю логику)
        left_color = '#42A5F5'   # цена за м² — голубой
        right_color = '#FB8C00'  # количество — оранжевый

        x_positions = list(range(1, len(labels) + 1))

        fig = go.Figure()

        for x, name, values, color, count in zip(x_positions, labels, price_data, colors, counts):
            stats_vals = calculate_statistics(values)
            if not stats_vals:
                continue

            q1 = stats_vals['q1']
            q3 = stats_vals['q3']
            mean_val = stats_vals['mean']
            outliers = stats_vals.get('outliers', [])

            height = max(q3 - q1, 0)

            # Цвет обводки — немного темнее заливки
            if color == '#A5D6A7':
                edge_color = '#66BB6A'
            elif color == '#90CAF9':
                edge_color = '#42A5F5'
            else:
                edge_color = '#546E7A'

            # Прямоугольник [Q1, Q3] как столбец
            fig.add_trace(go.Bar(
                x=[x],
                y=[height],
                base=[q1],
                width=0.4,
                marker=dict(
                    color=color,
                    line=dict(color=edge_color, width=1.4)
                ),
                customdata=[[stats_vals['min'], mean_val, stats_vals['max'], name]],
                hovertemplate=(
                    "%{customdata[3]}<br>"
                    "Мин: %{customdata[0]:,.0f} руб.<br>"
                    "Сред: %{customdata[1]:,.0f} руб.<br>"
                    "Макс: %{customdata[2]:,.0f} руб.<extra></extra>"
                ),
                showlegend=False
            ))

            # Линия среднего значения
            fig.add_trace(go.Scatter(
                x=[x - 0.2, x + 0.2],
                y=[mean_val, mean_val],
                mode='lines',
                line=dict(color=edge_color, width=1.6),
                hoverinfo='skip',
                showlegend=False
            ))

            # Выбросы убраны по запросу пользователя

            # Точка количества квартир (правая ось)
            if count > 0:
                fig.add_trace(go.Scatter(
                    x=[x],
                    y=[count],
                    mode='markers',
                    marker=dict(
                        color=right_color,
                        size=9
                    ),
                    hovertemplate=(
                        f"{name}<br>"
                        "Количество квартир: %{y}<extra></extra>"
                    ),
                    yaxis='y2',
                    showlegend=False
                ))

        # Определяем разумный диапазон для оси количества, чтобы точки целиком попадали в область графика
        max_count = max([c for c in counts if c > 0], default=1)
        # Чуть опускаем нижнюю границу ниже нуля, чтобы маркеры не "обрезались" по низу
        y2_min = -max(1, max_count * 0.1)
        y2_max = max_count * 1.1
        y2_range = [y2_min, y2_max]

        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=x_positions,
                ticktext=labels,
                tickangle=-90,
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                title=dict(
                    text='Цена за м², руб.',
                    font=dict(color=left_color)
                ),
                tickfont=dict(color=left_color),
                tickformat=',.0f',
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis2=dict(
                title=dict(
                    text='Количество квартир',
                    font=dict(color=right_color)
                ),
                tickfont=dict(color=right_color),
                dtick=20,
                range=y2_range,
                overlaying='y',
                side='right'
            ),
            bargap=0.3,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=60, r=60, t=20, b=120),
            height=500,
            showlegend=False,
            hovermode='closest'
        )

        boxplots[area_type] = {
            'data': fig.to_dict()['data'],
            'layout': fig.to_dict()['layout'],
            'div_id': f'boxplot_{area_type}',
            'title': f'Цены за м², {area_type}'
        }

    return boxplots if boxplots else None


def build_characteristics(main_objects_data, competitor_objects_data):
    """Строит сводную таблицу характеристик по каждому ЖК.

    Для этажности выводим диапазон (мин–макс), для остальных параметров —
    все уникальные значения через запятую.
    """
    characteristics_map = {}

    def ensure_obj(name, is_main):
        if name not in characteristics_map:
            characteristics_map[name] = {
                'name': name,
                'is_main': is_main,
                'Застройщик': set(),
                'Район': set(),
                'Класс': set(),
                'Этажность': [],
                'Этажность_сырье': set(),
                'Срок сдачи': set(),
                'Тип дома': set(),
                'Отделка': set()
            }

    # Основные ЖК
    for object_name, apartments in main_objects_data.items():
        ensure_obj(object_name, True)
        obj = characteristics_map[object_name]
        for apt in apartments:
            for field in ['Застройщик', 'Район', 'Класс', 'Срок сдачи', 'Тип дома', 'Отделка']:
                val = apt.get(field)
                if val:
                    obj[field].add(str(val).strip())
            # Этажность обрабатываем отдельно
            floors_raw = apt.get('Этажность')
            if floors_raw:
                s = str(floors_raw).strip()
                obj['Этажность_сырье'].add(s)
                try:
                    # Пробуем разобрать как число
                    n = int(float(s.replace(',', '.')))
                    obj['Этажность'].append(n)
                except ValueError:
                    pass

    # Конкуренты
    for object_name, apartments in competitor_objects_data.items():
        ensure_obj(object_name, False)
        obj = characteristics_map[object_name]
        for apt in apartments:
            for field in ['Застройщик', 'Район', 'Класс', 'Срок сдачи', 'Тип дома', 'Отделка']:
                val = apt.get(field)
                if val:
                    obj[field].add(str(val).strip())
            floors_raw = apt.get('Этажность')
            if floors_raw:
                s = str(floors_raw).strip()
                obj['Этажность_сырье'].add(s)
                try:
                    n = int(float(s.replace(',', '.')))
                    obj['Этажность'].append(n)
                except ValueError:
                    pass

    result = []
    for name, obj in characteristics_map.items():
        # Преобразуем множества в строки
        row = {
            'Название ЖК': name,
            'is_main': obj['is_main']
        }
        for field in ['Застройщик', 'Район', 'Класс', 'Срок сдачи', 'Тип дома', 'Отделка']:
            values = sorted(v for v in obj[field] if v)
            row[field] = ', '.join(values) if values else ''

        # Этажность: диапазон, если есть числовые значения
        floors_nums = obj['Этажность']
        floors_text = ''
        if floors_nums:
            mn = min(floors_nums)
            mx = max(floors_nums)
            if mn == mx:
                floors_text = str(mn)
            else:
                floors_text = f'{mn}–{mx}'
        # Если есть нестандартные текстовые значения, добавим их
        extra_floors = sorted(v for v in obj['Этажность_сырье'] if v)
        if extra_floors:
            # избегаем дублирования чисел, уже вошедших в диапазон
            extra_clean = [v for v in extra_floors if v != floors_text]
            if floors_text and extra_clean:
                floors_text = f"{floors_text}, " + ', '.join(extra_clean)
            elif not floors_text:
                floors_text = ', '.join(extra_clean)

        row['Этажность'] = floors_text

        result.append(row)

    # Основные ЖК сначала, затем конкуренты, по алфавиту
    result.sort(key=lambda r: (not r.get('is_main', False), r.get('Название ЖК', '')))
    return result

def create_boxplot(group1, group2):
    """Создает boxplot для двух групп"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    data1 = group1['costs']
    data2 = group2['costs']
    
    positions = [1, 2]
    data = [data1, data2]
    
    bp = ax.boxplot(data, positions=positions, widths=0.6, vert=True, patch_artist=True,
                    showmeans=True, meanline=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    meanprops=dict(color='green', linewidth=2, linestyle='--'),
                    whiskerprops=dict(color='black', linewidth=1.5),
                    capprops=dict(color='black', linewidth=1.5))
    
    colors = ['lightblue', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Выбросы убраны по запросу пользователя
    
    ax.set_ylabel('Стоимость, руб.', fontsize=12, fontweight='bold')
    ax.set_xticks(positions)
    ax.set_xticklabels([group1['source'], group2['source']], fontsize=11, fontweight='bold')
    ax.set_title('Сравнение стоимости',
                fontsize=12, fontweight='bold', pad=15)
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    ax.grid(True, alpha=0.3, axis='y')
    
    return plot_to_base64(fig)

def create_histogram(group1, group2):
    """Создает наложенные гистограммы для двух групп"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    data1 = group1['costs']
    data2 = group2['costs']
    
    # Вычисляем общий диапазон для обеих групп
    all_data = data1 + data2
    min_val = min(all_data)
    max_val = max(all_data)
    
    # Создаем одинаковые границы бинов для обеих групп
    num_bins = 15
    bin_edges = np.linspace(min_val, max_val, num_bins + 1)
    
    ax.hist(data1, bins=bin_edges, alpha=0.6, label=group1['source'], 
           color='steelblue', edgecolor='black', linewidth=0.5)
    ax.hist(data2, bins=bin_edges, alpha=0.6, label=group2['source'],
           color='coral', edgecolor='black', linewidth=0.5)
    
    # Средние и медианы
    stats1 = group1['stats']
    stats2 = group2['stats']
    
    ax.axvline(stats1['mean'], color='blue', linestyle='--', linewidth=2)
    ax.axvline(stats2['mean'], color='red', linestyle='--', linewidth=2)
    ax.axvline(stats1['median'], color='darkblue', linestyle='-', linewidth=2)
    ax.axvline(stats2['median'], color='darkred', linestyle='-', linewidth=2)
    
    ax.set_xlabel('Стоимость, руб.', fontsize=12, fontweight='bold')
    ax.set_ylabel('Количество квартир', fontsize=12, fontweight='bold')
    ax.set_title('Распределение стоимости',
                fontsize=12, fontweight='bold', pad=15)
    
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}М'))
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(loc='upper right', fontsize=10)
    
    return plot_to_base64(fig)

# Регистрируем Blueprint для Аквилона
app.register_blueprint(akvilon_bp)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

