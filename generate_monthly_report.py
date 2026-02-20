#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Единый скрипт для генерации ежемесячного отчета по технической поддержке
Использование: python3 generate_monthly_report.py <месяц> <год> <путь_к_csv>
Пример: python3 generate_monthly_report.py 12 2025 "/Users/annarybkina/Downloads/Задачи-5 - Лист1.csv"
"""

import csv
import sys
import re
from datetime import datetime
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import base64
    from io import BytesIO
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    print("⚠ Предупреждение: matplotlib/numpy не установлены. Визуализации не будут созданы.")
    print("Установите: pip3 install matplotlib numpy")


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def parse_date(date_str):
    """Парсит дату в формате '28 дек. 2025'"""
    if not date_str or date_str.strip() == '':
        return None
    
    months = {
        'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
        'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
    }
    
    try:
        parts = date_str.strip().split()
        if len(parts) >= 3:
            day = int(parts[0])
            month_name = parts[1].lower()[:3]
            year = int(parts[2])
            month = months.get(month_name)
            if month:
                return datetime(year, month, day)
    except:
        pass
    return None


def is_external_user(developer):
    """Определяет, является ли пользователь внешним (prod) или внутренним (dev/demo)"""
    if not developer or developer.strip() == '':
        return None
    
    developer_lower = developer.lower()
    if 'allio dev' in developer_lower or 'allio demo' in developer_lower or developer_lower == 'demo':
        return False
    return True


def parse_time_minutes(time_str):
    """Парсит время в минутах из строки"""
    if not time_str or time_str.strip() == '':
        return None
    try:
        return int(float(str(time_str).strip()))
    except:
        return None


def categorize_first_reply(minutes):
    """Категоризирует первую реакцию"""
    if minutes is None:
        return "Неизвестно"
    if minutes < 15:
        return "Меньше 15м"
    elif minutes < 60:
        return "От 15м до 1ч"
    elif minutes < 1440:
        return "от 1ч до 1д"
    else:
        return "Более 1д"


def categorize_resolution_time(minutes):
    """Категоризирует время решения"""
    if minutes is None:
        return "Неизвестно"
    if minutes < 60:
        return "Меньше 1ч"
    elif minutes < 1440:
        return "От 1ч до 1д"
    elif minutes < 10080:
        return "От 1д до 1н"
    else:
        return "Более 1н"


def plot_to_base64(fig):
    """Конвертирует matplotlib figure в base64 строку"""
    if not HAS_VISUALIZATION:
        return None
    try:
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_base64
    except Exception as e:
        print(f"Ошибка при конвертации графика: {e}")
        return None


# ==================== ЗАГРУЗКА ДАННЫХ ====================

def load_data(file_path):
    """Загружает данные из CSV файла"""
    requests = []
    encodings = ['utf-8', 'cp1251', 'windows-1251', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    normalized_row = {k.strip(): v for k, v in row.items()}
                    
                    created_date = parse_date(normalized_row.get('Создана', ''))
                    request_type = normalized_row.get('Тип', '').strip()
                    developer = normalized_row.get('Застройщик', '').strip()
                    
                    first_reply_min = parse_time_minutes(normalized_row.get('Первая реакция', ''))
                    resolution_min = parse_time_minutes(normalized_row.get('Время решения', ''))
                    
                    requests.append({
                        'id': normalized_row.get('ID задачи', ''),
                        'created': created_date,
                        'type': request_type,
                        'developer': developer,
                        'is_external': is_external_user(developer),
                        'first_reply_min': first_reply_min,
                        'resolution_min': resolution_min,
                        'first_reply_category': categorize_first_reply(first_reply_min),
                        'resolution_category': categorize_resolution_time(resolution_min),
                        'raw': normalized_row
                    })
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return []
    
    return requests


# ==================== РАСЧЕТ СТАТИСТИКИ ====================

def filter_by_month_year(requests, month, year):
    """Фильтрует обращения за указанный месяц и год"""
    return [r for r in requests if r['created'] and r['created'].year == year and r['created'].month == month]


def filter_by_year(requests, year):
    """Фильтрует обращения за год"""
    return [r for r in requests if r['created'] and r['created'].year == year]


def calculate_monthly_stats(requests):
    """Рассчитывает статистику за месяц"""
    total = len(requests)
    external = len([r for r in requests if r['is_external'] is True])
    internal = len([r for r in requests if r['is_external'] is False])
    
    return {
        'total': total,
        'external': external,
        'internal': internal
    }


def calculate_yearly_stats(requests, target_month, target_year):
    """Рассчитывает статистику по месяцам за год"""
    monthly_stats = defaultdict(lambda: {'total': 0, 'external': 0, 'internal': 0})
    
    for req in requests:
        if req['created']:
            month_key = req['created'].month
            monthly_stats[month_key]['total'] += 1
            if req['is_external'] is True:
                monthly_stats[month_key]['external'] += 1
            elif req['is_external'] is False:
                monthly_stats[month_key]['internal'] += 1
    
    return monthly_stats


def calculate_type_ratio(requests):
    """Рассчитывает соотношение типов обращений"""
    type_stats = defaultdict(lambda: {'total': 0, 'external': 0, 'internal': 0})
    
    for req in requests:
        req_type = req['type']
        if req_type:
            type_stats[req_type]['total'] += 1
            if req['is_external'] is True:
                type_stats[req_type]['external'] += 1
            elif req['is_external'] is False:
                type_stats[req_type]['internal'] += 1
    
    total_all = {
        'total': sum(s['total'] for s in type_stats.values()),
        'external': sum(s['external'] for s in type_stats.values()),
        'internal': sum(s['internal'] for s in type_stats.values())
    }
    
    return type_stats, total_all


def calculate_type_dynamics(requests, target_month, target_year):
    """Рассчитывает динамику по типам (только внешние)"""
    monthly_type_stats = defaultdict(lambda: defaultdict(int))
    
    for req in requests:
        if req['is_external'] is True and req['created']:
            month = req['created'].month
            req_type = req['type']
            if req_type:
                monthly_type_stats[month][req_type] += 1
    
    return monthly_type_stats


def calculate_sla_stats(requests):
    """Рассчитывает статистику по SLA"""
    first_reply_stats = defaultdict(lambda: defaultdict(int))
    resolution_stats = defaultdict(lambda: defaultdict(int))
    
    for req in requests:
        req_type = req['type']
        if req_type:
            first_reply_stats[req_type][req['first_reply_category']] += 1
            resolution_stats[req_type][req['resolution_category']] += 1
    
    return first_reply_stats, resolution_stats


# ==================== ВИЗУАЛИЗАЦИИ ====================

def create_monthly_dynamics_chart(yearly_stats):
    """Создает график динамики обращений по месяцам"""
    if not HAS_VISUALIZATION:
        return None
    
    month_names = {
        1: 'Янв', 2: 'Фев', 3: 'Мар', 4: 'Апр', 5: 'Май', 6: 'Июн',
        7: 'Июл', 8: 'Авг', 9: 'Сен', 10: 'Окт', 11: 'Ноя', 12: 'Дек'
    }
    
    months = []
    totals = []
    externals = []
    internals = []
    
    for month in range(1, 13):
        if month in yearly_stats:
            months.append(month_names[month])
            stats = yearly_stats[month]
            totals.append(stats['total'])
            externals.append(stats['external'])
            internals.append(stats['internal'])
    
    fig, ax = plt.subplots(figsize=(14, 8))
    x = np.arange(len(months))
    width = 0.35
    
    ax.bar(x - width/2, externals, width, label='Внешние', color='#2e7d32', alpha=0.8)
    ax.bar(x + width/2, internals, width, label='Внутренние', color='#d32f2f', alpha=0.8)
    ax.plot(x, totals, 'o-', color='#1976d2', linewidth=2, markersize=8, label='Всего')
    
    ax.set_xlabel('Месяц', fontsize=12)
    ax.set_ylabel('Количество обращений', fontsize=12)
    ax.set_title('Динамика количества обращений по месяцам', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    return plot_to_base64(fig)


def create_type_dynamics_chart(type_dynamics):
    """Создает график динамики по типам (только внешние)"""
    if not HAS_VISUALIZATION:
        return None
    
    month_names = {
        1: 'Янв', 2: 'Фев', 3: 'Мар', 4: 'Апр', 5: 'Май', 6: 'Июн',
        7: 'Июл', 8: 'Авг', 9: 'Сен', 10: 'Окт', 11: 'Ноя', 12: 'Дек'
    }
    
    months = []
    questions = []
    problems = []
    wishes = []
    
    for month in range(1, 13):
        if month in type_dynamics:
            months.append(month_names[month])
            month_data = type_dynamics[month]
            questions.append(month_data.get('Вопрос', 0))
            problems.append(month_data.get('Проблема', 0))
            wishes.append(month_data.get('Пожелание', 0))
    
    fig, ax = plt.subplots(figsize=(14, 8))
    x = np.arange(len(months))
    width = 0.25
    
    ax.bar(x - width, questions, width, label='Вопрос', color='#1976d2', alpha=0.8)
    ax.bar(x, problems, width, label='Проблема', color='#d32f2f', alpha=0.8)
    ax.bar(x + width, wishes, width, label='Пожелание', color='#388e3c', alpha=0.8)
    
    ax.set_xlabel('Месяц', fontsize=12)
    ax.set_ylabel('Количество обращений', fontsize=12)
    ax.set_title('Динамика по типам обращений (только внешние)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    return plot_to_base64(fig)


def create_first_reply_pie_charts(first_reply_stats):
    """Создает круговые диаграммы для первой реакции"""
    if not HAS_VISUALIZATION:
        return None
    
    types = ['Вопрос', 'Проблема', 'Пожелание']
    colors_map = {
        'Меньше 15м': '#4caf50',
        'От 15м до 1ч': '#ff9800',
        'от 1ч до 1д': '#f44336'
    }
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, req_type in enumerate(types):
        data = first_reply_stats.get(req_type, {})
        labels = []
        sizes = []
        colors = []
        
        for cat in ['Меньше 15м', 'От 15м до 1ч', 'от 1ч до 1д']:
            if data.get(cat, 0) > 0:
                labels.append(cat)
                sizes.append(data[cat])
                colors.append(colors_map[cat])
        
        if sizes:
            wedges, texts, autotexts = axes[idx].pie(
                sizes, labels=labels, colors=colors,
                autopct='%1.1f%%', startangle=90,
                textprops={'fontsize': 10, 'fontweight': 'bold'}
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        total = sum(data.values())
        axes[idx].set_title(f'{req_type}\n(Всего: {total})', 
                           fontsize=12, fontweight='bold', pad=15)
    
    plt.suptitle('Первая реакция по типам обращений', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    return plot_to_base64(fig)


def create_resolution_pie_charts(resolution_stats):
    """Создает круговые диаграммы для времени решения"""
    if not HAS_VISUALIZATION:
        return None
    
    types = ['Вопрос', 'Проблема', 'Пожелание']
    colors_map = {
        'Меньше 1ч': '#4caf50',
        'От 1ч до 1д': '#8bc34a',
        'От 1д до 1н': '#ff9800',
        'Более 1н': '#f44336',
        'Неизвестно': '#9e9e9e'
    }
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, req_type in enumerate(types):
        data = resolution_stats.get(req_type, {})
        labels = []
        sizes = []
        colors = []
        
        for cat in ['Меньше 1ч', 'От 1ч до 1д', 'От 1д до 1н', 'Более 1н', 'Неизвестно']:
            if data.get(cat, 0) > 0:
                labels.append(cat)
                sizes.append(data[cat])
                colors.append(colors_map[cat])
        
        if sizes:
            wedges, texts, autotexts = axes[idx].pie(
                sizes, labels=labels, colors=colors,
                autopct='%1.1f%%', startangle=90,
                textprops={'fontsize': 9, 'fontweight': 'bold'}
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            for text in texts:
                text.set_fontsize(9)
        
        total = sum(data.values())
        axes[idx].set_title(f'{req_type}\n(Всего: {total})', 
                           fontsize=12, fontweight='bold', pad=15)
    
    plt.suptitle('Время решения по типам обращений', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    return plot_to_base64(fig)


# ==================== ГЕНЕРАЦИЯ ВЫВОДОВ ====================

def generate_conclusions(type_dynamics, monthly_stats, target_month, target_year):
    """Генерирует аналитические выводы"""
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    current_month = target_month
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_prev_month = prev_month - 1 if prev_month > 1 else 12
    
    current_data = type_dynamics.get(current_month, {})
    prev_data = type_dynamics.get(prev_month, {})
    prev_prev_data = type_dynamics.get(prev_prev_month, {})
    
    current_questions = current_data.get('Вопрос', 0)
    prev_questions = prev_data.get('Вопрос', 0)
    current_problems = current_data.get('Проблема', 0)
    prev_problems = prev_data.get('Проблема', 0)
    current_wishes = current_data.get('Пожелание', 0)
    prev_wishes = prev_data.get('Пожелание', 0)
    
    # Статистика за год
    all_questions = [type_dynamics[i].get('Вопрос', 0) for i in range(1, 13) if i in type_dynamics]
    all_problems = [type_dynamics[i].get('Проблема', 0) for i in range(1, 13) if i in type_dynamics]
    all_wishes = [type_dynamics[i].get('Пожелание', 0) for i in range(1, 13) if i in type_dynamics]
    
    max_questions = max(all_questions) if all_questions else 0
    min_questions = min(all_questions) if all_questions else 0
    avg_questions = sum(all_questions) / len(all_questions) if all_questions else 0
    
    max_problems = max(all_problems) if all_problems else 0
    min_problems = min(all_problems) if all_problems else 0
    avg_problems = sum(all_problems) / len(all_problems) if all_problems else 0
    
    max_wishes = max(all_wishes) if all_wishes else 0
    min_wishes = min(all_wishes) if all_wishes else 0
    avg_wishes = sum(all_wishes) / len(all_wishes) if all_wishes else 0
    
    current_external = monthly_stats.get(current_month, {}).get('external', 0)
    
    conclusions = []
    conclusions.append("<h3>Вопросы</h3>")
    conclusions.append("<ul>")
    
    if current_questions == prev_questions:
        conclusions.append(f"<li>В {month_names[current_month].lower()} количество вопросов осталось на прежнем уровне — {current_questions} (как и в {month_names[prev_month].lower()}).</li>")
    elif current_questions > prev_questions:
        change = current_questions - prev_questions
        conclusions.append(f"<li>В {month_names[current_month].lower()} количество вопросов выросло на {change} до {current_questions} (после {prev_questions} в {month_names[prev_month].lower()}).</li>")
    else:
        change = prev_questions - current_questions
        conclusions.append(f"<li>В {month_names[current_month].lower()} количество вопросов снизилось на {change} до {current_questions} (после {prev_questions} в {month_names[prev_month].lower()}).</li>")
    
    if current_questions == max_questions:
        conclusions.append(f"<li>Это максимальный показатель за весь год (максимум: {max_questions}, среднее за год: {avg_questions:.1f}).</li>")
    
    if prev_prev_month in type_dynamics:
        prev_prev_questions = type_dynamics[prev_prev_month].get('Вопрос', 0)
        if current_questions > prev_prev_questions:
            change = current_questions - prev_prev_questions
            pct = (change / prev_prev_questions * 100) if prev_prev_questions > 0 else 0
            conclusions.append(f"<li>По сравнению с {month_names[prev_prev_month].lower()} наблюдается рост на {change} обращений (+{pct:.1f}%), что может быть связано с закрытием периода и необходимостью решить накопившиеся вопросы.</li>")
    
    question_share = (current_questions / current_external * 100) if current_external > 0 else 0
    conclusions.append(f"<li>Вопросы составляют {question_share:.1f}% от всех внешних обращений в {month_names[current_month].lower()} — это доминирующий тип обращений.</li>")
    conclusions.append("</ul>")
    
    conclusions.append("<h3>Проблемы</h3>")
    conclusions.append("<ul>")
    
    if current_problems == prev_problems:
        conclusions.append(f"<li>Количество проблем в {month_names[current_month].lower()} осталось на уровне {month_names[prev_month].lower()} — {current_problems} (только внешние).</li>")
    elif current_problems < prev_problems:
        change = prev_problems - current_problems
        conclusions.append(f"<li>Количество проблем в {month_names[current_month].lower()} снизилось на {change} до {current_problems} (после {prev_problems} в {month_names[prev_month].lower()}, только внешние).</li>")
    else:
        change = current_problems - prev_problems
        conclusions.append(f"<li>Количество проблем в {month_names[current_month].lower()} выросло на {change} до {current_problems} (после {prev_problems} в {month_names[prev_month].lower()}, только внешние).</li>")
    
    if current_problems == min_problems:
        conclusions.append(f"<li>Это минимальный показатель за весь год (минимум: {min_problems}, среднее за год: {avg_problems:.1f}).</li>")
    
    if prev_prev_month in type_dynamics:
        prev_prev_problems = type_dynamics[prev_prev_month].get('Проблема', 0)
        if current_problems < prev_prev_problems:
            change = prev_prev_problems - current_problems
            pct = (change / prev_prev_problems * 100) if prev_prev_problems > 0 else 0
            conclusions.append(f"<li>По сравнению с {month_names[prev_prev_month].lower()} количество проблем снизилось на {change} (-{pct:.1f}%), что говорит о стабилизации системы и уменьшении количества багов.</li>")
    
    problem_share = (current_problems / current_external * 100) if current_external > 0 else 0
    conclusions.append(f"<li>Доля проблем ко всем внешним обращениям составляет {problem_share:.1f}% — это самый низкий процент среди типов обращений.</li>")
    conclusions.append("</ul>")
    
    conclusions.append("<h3>Пожелания</h3>")
    conclusions.append("<ul>")
    
    if current_wishes == prev_wishes:
        conclusions.append(f"<li>Количество пожеланий в {month_names[current_month].lower()} осталось на уровне {month_names[prev_month].lower()} — {current_wishes} (только внешние).</li>")
    elif current_wishes > prev_wishes:
        change = current_wishes - prev_wishes
        conclusions.append(f"<li>В {month_names[current_month].lower()} количество пожеланий выросло на {change} до {current_wishes} (после {prev_wishes} в {month_names[prev_month].lower()}).</li>")
    else:
        change = prev_wishes - current_wishes
        conclusions.append(f"<li>В {month_names[current_month].lower()} количество пожеланий снизилось на {change} до {current_wishes} (после {prev_wishes} в {month_names[prev_month].lower()}).</li>")
    
    if prev_prev_month in type_dynamics:
        prev_prev_wishes = type_dynamics[prev_prev_month].get('Пожелание', 0)
        if current_wishes > prev_prev_wishes:
            change = current_wishes - prev_prev_wishes
            pct = (change / prev_prev_wishes * 100) if prev_prev_wishes > 0 else 0
            conclusions.append(f"<li>По сравнению с {month_names[prev_prev_month].lower()} наблюдается рост на {change} обращений (+{pct:.1f}%), что может быть связано с активным использованием системы и выявлением потребностей в улучшениях.</li>")
    
    wish_share = (current_wishes / current_external * 100) if current_external > 0 else 0
    conclusions.append(f"<li>Пожелания составляют {wish_share:.1f}% от всех внешних обращений.</li>")
    
    if current_wishes > avg_wishes:
        conclusions.append(f"<li>Количество пожеланий ({current_wishes}) выше среднего за год ({avg_wishes:.1f}), что указывает на активность пользователей в плане предложений по улучшению функционала.</li>")
    conclusions.append("</ul>")
    
    conclusions.append("<h3>Итоговые выводы</h3>")
    conclusions.append("<ul>")
    
    total_ext_current = current_questions + current_problems + current_wishes
    total_ext_prev = prev_questions + prev_problems + prev_wishes
    
    if total_ext_current == total_ext_prev:
        conclusions.append(f"<li>Общий поток внешних обращений в {month_names[current_month].lower()} стабилизировался на уровне {total_ext_current} обращений (как в {month_names[prev_month].lower()}).</li>")
    else:
        change_total = total_ext_current - total_ext_prev
        conclusions.append(f"<li>Общий поток внешних обращений в {month_names[current_month].lower()} {'вырос' if change_total > 0 else 'снизился'} на {abs(change_total)} до {total_ext_current} обращений.</li>")
    
    if current_questions > (current_problems + current_wishes):
        conclusions.append(f"<li>Структура обращений смещена в сторону вопросов ({question_share:.1f}% от всех обращений), что указывает на потребность пользователей в консультациях и поддержке.</li>")
    
    if current_problems < avg_problems:
        conclusions.append(f"<li>Количество проблем ({current_problems}) ниже среднего за год ({avg_problems:.1f}), что является положительным показателем стабильности системы.</li>")
    
    if current_questions == max_questions:
        conclusions.append(f"<li>Рекордное количество вопросов за год ({current_questions}) может быть связано с закрытием периода, когда пользователи активно закрывают накопившиеся задачи и обращаются за консультациями.</li>")
    
    conclusions.append("</ul>")
    
    return "\n".join(conclusions)


# ==================== ГЕНЕРАЦИЯ HTML ====================

def generate_html_report(monthly_requests, all_requests, target_month, target_year, output_dir):
    """Генерирует полный HTML отчет"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    # Шаг 1: Статистика за месяц
    monthly_stats_data = calculate_monthly_stats(monthly_requests)
    
    # Шаг 2: Статистика за год
    yearly_requests = filter_by_year(all_requests, target_year)
    yearly_stats = calculate_yearly_stats(yearly_requests, target_month, target_year)
    yearly_stats[target_month] = monthly_stats_data
    
    total_year = sum(s['total'] for s in yearly_stats.values())
    external_year = sum(s['external'] for s in yearly_stats.values())
    internal_year = sum(s['internal'] for s in yearly_stats.values())
    
    # Шаг 3: Соотношение типов
    type_ratio, type_total = calculate_type_ratio(monthly_requests)
    
    # Шаг 4: Динамика по типам
    type_dynamics = calculate_type_dynamics(yearly_requests, target_month, target_year)
    
    # Шаг 5: Выводы
    conclusions_html = generate_conclusions(type_dynamics, yearly_stats, target_month, target_year)
    
    # Шаг 6: SLA
    first_reply_stats, resolution_stats = calculate_sla_stats(monthly_requests)
    
    # Визуализации
    chart1_base64 = create_monthly_dynamics_chart(yearly_stats)
    chart2_base64 = create_type_dynamics_chart(type_dynamics)
    chart3_base64 = create_first_reply_pie_charts(first_reply_stats)
    chart4_base64 = create_resolution_pie_charts(resolution_stats)
    
    # Общие итоги SLA
    total_under_15 = sum(first_reply_stats[t].get('Меньше 15м', 0) for t in first_reply_stats)
    total_all_sla = sum(sum(first_reply_stats[t].values()) for t in first_reply_stats)
    overall_pct = (total_under_15 / total_all_sla * 100) if total_all_sla > 0 else 0
    
    # Минималистичный CSS
    css = """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #000;
            background-color: #fff;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        h1 {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 30px;
            color: #000;
        }
        
        h2 {
            font-size: 22px;
            font-weight: bold;
            margin-top: 50px;
            margin-bottom: 20px;
            color: #000;
        }
        
        h3 {
            font-size: 16px;
            font-weight: bold;
            margin-top: 25px;
            margin-bottom: 15px;
            color: #000;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0 40px 0;
            background-color: #fff;
            border: 1px solid #e0e0e0;
        }
        
        th {
            background-color: #f5f5f5;
            color: #000;
            padding: 12px 15px;
            text-align: left;
            font-weight: bold;
            font-size: 14px;
            border-bottom: 2px solid #000;
        }
        
        td {
            padding: 10px 15px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 14px;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        .external, .share, strong {
            font-weight: bold;
            color: #000;
        }
        
        .chart-container {
            background-color: #fff;
            padding: 30px 0;
            margin: 40px 0;
            text-align: center;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #e0e0e0;
        }
        
        .chart-container h3 {
            margin-bottom: 20px;
            font-size: 16px;
            font-weight: bold;
        }
        
        .conclusions {
            background-color: #fff;
            padding: 0;
            margin: 30px 0;
        }
        
        .conclusions ul {
            margin: 15px 0;
            padding-left: 25px;
        }
        
        .conclusions li {
            margin: 8px 0;
            line-height: 1.7;
        }
        
        .conclusions p {
            margin: 15px 0;
            line-height: 1.7;
        }
        
        .stat-box {
            background-color: #fff;
            padding: 0;
            margin: 25px 0;
        }
        
        .stat-item {
            margin: 12px 0;
            font-size: 14px;
        }
        
        .stat-number {
            font-weight: bold;
            color: #000;
        }
    </style>
    """
    
    # Генерация HTML
    html_parts = []
    html_parts.append("<!DOCTYPE html>")
    html_parts.append("<html lang='ru'>")
    html_parts.append("<head>")
    html_parts.append("    <meta charset='UTF-8'>")
    html_parts.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html_parts.append(f"    <title>Отчет по технической поддержке - {month_names[target_month]} {target_year}</title>")
    html_parts.append(css)
    html_parts.append("</head>")
    html_parts.append("<body>")
    html_parts.append(f"    <h1>Отчет по технической поддержке</h1>")
    html_parts.append(f"    <h2>{month_names[target_month]} {target_year}</h2>")
    
    # Шаг 1
    html_parts.append("    <div class='stat-box'>")
    html_parts.append("        <h3>1. Статистика обращений за месяц</h3>")
    html_parts.append(f"        <div class='stat-item'>• Всего обращений за {month_names[target_month].lower()} — <span class='stat-number'>{monthly_stats_data['total']}</span></div>")
    html_parts.append(f"        <div class='stat-item'>• Внешние пользователи (prod) — <span class='stat-number'>{monthly_stats_data['external']}</span></div>")
    html_parts.append(f"        <div class='stat-item'>• Внутренние пользователи (dev и demo) — <span class='stat-number'>{monthly_stats_data['internal']}</span></div>")
    html_parts.append(f"        <div class='stat-item'>• Обращений за {target_year} год — <span class='stat-number'>{total_year}</span> (внешних - {external_year}, внутренних - {internal_year})</div>")
    html_parts.append("    </div>")
    
    # Шаг 2
    html_parts.append(f"    <h2>2. Динамика количества обращений по месяцам</h2>")
    html_parts.append("    <table>")
    html_parts.append("        <thead>")
    html_parts.append("            <tr><th>Месяц</th><th>Общее кол-во</th><th>Внешние</th><th>Внутренние</th><th>Прирост (внешние)</th></tr>")
    html_parts.append("        </thead>")
    html_parts.append("        <tbody>")
    
    prev_external = None
    for month in range(1, 13):
        if month in yearly_stats:
            stats = yearly_stats[month]
            growth = ""
            if prev_external is not None and prev_external > 0:
                growth_pct = ((stats['external'] - prev_external) / prev_external) * 100
                growth = f"{growth_pct:+.2f}%"
            elif prev_external is None:
                growth = "0%"
            
            html_parts.append(f"            <tr>")
            html_parts.append(f"                <td><strong>{month_names[month]}</strong></td>")
            html_parts.append(f"                <td>{stats['total']}</td>")
            html_parts.append(f"                <td><strong>{stats['external']}</strong></td>")
            html_parts.append(f"                <td>{stats['internal']}</td>")
            html_parts.append(f"                <td>{growth}</td>")
            html_parts.append(f"            </tr>")
            prev_external = stats['external']
    
    html_parts.append("        </tbody>")
    html_parts.append("    </table>")
    
    if chart1_base64:
        html_parts.append("    <div class='chart-container'>")
        html_parts.append("        <h3>Визуализация динамики обращений</h3>")
        html_parts.append(f"        <img src='data:image/png;base64,{chart1_base64}' alt='Динамика обращений'>")
        html_parts.append("    </div>")
    
    # Шаг 3
    html_parts.append("    <h2>3. Соотношение типов обращений</h2>")
    html_parts.append("    <table>")
    html_parts.append("        <thead>")
    html_parts.append("            <tr><th>Тип</th><th>Общее кол-во</th><th>Внешние</th><th>Внутренние</th><th>Доля внешних от общего за месяц</th></tr>")
    html_parts.append("        </thead>")
    html_parts.append("        <tbody>")
    
    for req_type in ['Вопрос', 'Проблема', 'Пожелание']:
        if req_type in type_ratio:
            stats = type_ratio[req_type]
            share = (stats['external'] / stats['total'] * 100) if stats['total'] > 0 else 0
            html_parts.append(f"            <tr>")
            html_parts.append(f"                <td><strong>{req_type}</strong></td>")
            html_parts.append(f"                <td>{stats['total']}</td>")
            html_parts.append(f"                <td><strong>{stats['external']}</strong></td>")
            html_parts.append(f"                <td>{stats['internal']}</td>")
            html_parts.append(f"                <td>{share:.2f}%</td>")
            html_parts.append(f"            </tr>")
    
    total_share = (type_total['external'] / type_total['total'] * 100) if type_total['total'] > 0 else 0
    html_parts.append(f"            <tr style='background-color: #f5f5f5; font-weight: bold;'>")
    html_parts.append(f"                <td>Всего</td>")
    html_parts.append(f"                <td>{type_total['total']}</td>")
    html_parts.append(f"                <td>{type_total['external']}</td>")
    html_parts.append(f"                <td>{type_total['internal']}</td>")
    html_parts.append(f"                <td>{total_share:.2f}%</td>")
    html_parts.append(f"            </tr>")
    html_parts.append("        </tbody>")
    html_parts.append("    </table>")
    
    # Шаг 4
    html_parts.append("    <h2>4. Динамика по типам (только внешние)</h2>")
    html_parts.append("    <table>")
    html_parts.append("        <thead>")
    html_parts.append("            <tr><th>Месяц</th><th>Вопрос</th><th>Проблема</th><th>Пожелание</th></tr>")
    html_parts.append("        </thead>")
    html_parts.append("        <tbody>")
    
    for month in range(1, 13):
        if month in type_dynamics:
            month_data = type_dynamics[month]
            html_parts.append(f"            <tr>")
            html_parts.append(f"                <td><strong>{month_names[month]}</strong></td>")
            html_parts.append(f"                <td>{month_data.get('Вопрос', 0)}</td>")
            html_parts.append(f"                <td>{month_data.get('Проблема', 0)}</td>")
            html_parts.append(f"                <td>{month_data.get('Пожелание', 0)}</td>")
            html_parts.append(f"            </tr>")
    
    html_parts.append("        </tbody>")
    html_parts.append("    </table>")
    
    if chart2_base64:
        html_parts.append("    <div class='chart-container'>")
        html_parts.append("        <h3>Визуализация динамики по типам</h3>")
        html_parts.append(f"        <img src='data:image/png;base64,{chart2_base64}' alt='Динамика по типам'>")
        html_parts.append("    </div>")
    
    # Шаг 5
    html_parts.append("    <h2>5. Выводы по динамике обращений (внешние)</h2>")
    html_parts.append("    <div class='conclusions'>")
    html_parts.append(conclusions_html)
    html_parts.append("    </div>")
    
    # Шаг 6
    html_parts.append("    <h2>6. Таблицы по SLA</h2>")
    html_parts.append("    <h3>Первая реакция</h3>")
    html_parts.append("    <table>")
    html_parts.append("        <thead>")
    html_parts.append("            <tr><th>Тип обращения</th><th>Меньше 15м</th><th>От 15м до 1ч</th><th>от 1ч до 1д</th></tr>")
    html_parts.append("        </thead>")
    html_parts.append("        <tbody>")
    
    for req_type in ['Вопрос', 'Проблема', 'Пожелание']:
        if req_type in first_reply_stats:
            stats = first_reply_stats[req_type]
            html_parts.append(f"            <tr>")
            html_parts.append(f"                <td><strong>{req_type}</strong></td>")
            html_parts.append(f"                <td>{stats.get('Меньше 15м', 0)}</td>")
            html_parts.append(f"                <td>{stats.get('От 15м до 1ч', 0)}</td>")
            html_parts.append(f"                <td>{stats.get('от 1ч до 1д', 0)}</td>")
            html_parts.append(f"            </tr>")
    
    html_parts.append("        </tbody>")
    html_parts.append("    </table>")
    
    if chart3_base64:
        html_parts.append("    <div class='chart-container'>")
        html_parts.append("        <h3>Визуализация: Первая реакция</h3>")
        html_parts.append(f"        <img src='data:image/png;base64,{chart3_base64}' alt='Первая реакция по типам'>")
        html_parts.append("    </div>")
    
    html_parts.append("    <h3>Время решения</h3>")
    html_parts.append("    <table>")
    html_parts.append("        <thead>")
    html_parts.append("            <tr><th>Тип обращения</th><th>Меньше 1ч</th><th>От 1ч до 1д</th><th>От 1д до 1н</th><th>Более 1н</th><th>Неизвестно</th></tr>")
    html_parts.append("        </thead>")
    html_parts.append("        <tbody>")
    
    for req_type in ['Вопрос', 'Проблема', 'Пожелание']:
        if req_type in resolution_stats:
            stats = resolution_stats[req_type]
            html_parts.append(f"            <tr>")
            html_parts.append(f"                <td><strong>{req_type}</strong></td>")
            html_parts.append(f"                <td>{stats.get('Меньше 1ч', 0)}</td>")
            html_parts.append(f"                <td>{stats.get('От 1ч до 1д', 0)}</td>")
            html_parts.append(f"                <td>{stats.get('От 1д до 1н', 0)}</td>")
            html_parts.append(f"                <td>{stats.get('Более 1н', 0)}</td>")
            html_parts.append(f"                <td>{stats.get('Неизвестно', 0)}</td>")
            html_parts.append(f"            </tr>")
    
    html_parts.append("        </tbody>")
    html_parts.append("    </table>")
    
    if chart4_base64:
        html_parts.append("    <div class='chart-container'>")
        html_parts.append("        <h3>Визуализация: Время решения</h3>")
        html_parts.append(f"        <img src='data:image/png;base64,{chart4_base64}' alt='Время решения по типам'>")
        html_parts.append("    </div>")
    
    # Шаг 7: Общие итоги
    html_parts.append("    <h2>7. Общие итоги</h2>")
    html_parts.append("    <div class='conclusions'>")
    html_parts.append(f"        <p><strong>Большинство обращений ({overall_pct:.2f}%) получают ответ в течение первых 15 минут.</strong></p>")
    html_parts.append("        <p>Проблемы решаются быстрее других типов, а вопросы — наиболее длительные (поставлена задача по воркфлоу, пока на паузе из-за более высоких приоритетов других задач).</p>")
    html_parts.append("        <h3>По типам:</h3>")
    html_parts.append("        <ul>")
    
    for req_type in ['Вопрос', 'Проблема', 'Пожелание']:
        if req_type in first_reply_stats:
            stats = first_reply_stats[req_type]
            total_type = sum(stats.values())
            under_15 = stats.get('Меньше 15м', 0)
            if total_type > 0:
                pct = (under_15 / total_type) * 100
                html_parts.append(f"            <li><strong>{req_type}:</strong> {under_15} из {total_type} ({pct:.2f}%) — ответ менее чем за 15 минут.</li>")
    
    html_parts.append("        </ul>")
    html_parts.append("        <p>Лишь единичные случаи требуют большего времени на первичную реакцию — чаще всего это обращения, где нужно более глубокое тестирование или уточнение у разработчиков.</p>")
    html_parts.append("    </div>")
    
    html_parts.append("</body>")
    html_parts.append("</html>")
    
    return "\n".join(html_parts)


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def main():
    """Основная функция"""
    if len(sys.argv) < 4:
        print("Использование: python3 generate_monthly_report.py <месяц> <год> <путь_к_csv>")
        print("Пример: python3 generate_monthly_report.py 12 2025 \"/Users/annarybkina/Downloads/Задачи-5 - Лист1.csv\"")
        sys.exit(1)
    
    try:
        target_month = int(sys.argv[1])
        target_year = int(sys.argv[2])
        csv_path = Path(sys.argv[3])
    except (ValueError, IndexError):
        print("Ошибка: неверные параметры")
        print("Месяц должен быть числом от 1 до 12")
        print("Год должен быть числом")
        sys.exit(1)
    
    if not csv_path.exists():
        print(f"Ошибка: файл не найден: {csv_path}")
        sys.exit(1)
    
    if target_month < 1 or target_month > 12:
        print("Ошибка: месяц должен быть от 1 до 12")
        sys.exit(1)
    
    print(f"Загрузка данных из {csv_path}...")
    all_requests = load_data(csv_path)
    print(f"Загружено обращений: {len(all_requests)}")
    
    print(f"Фильтрация данных за {target_month}/{target_year}...")
    monthly_requests = filter_by_month_year(all_requests, target_month, target_year)
    print(f"Обращений за месяц: {len(monthly_requests)}")
    
    if len(monthly_requests) == 0:
        print("⚠ Предупреждение: не найдено обращений за указанный месяц")
        print("Проверьте формат дат в CSV файле")
    
    print("Генерация отчета...")
    
    # Определяем путь для сохранения
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    output_dir = Path("/Users/annarybkina/Desktop/Allio/ИИ Цены")
    html_report = generate_html_report(
        monthly_requests, 
        all_requests, 
        target_month, 
        target_year,
        output_dir
    )
    
    output_file = output_dir / f"Отчет_техподдержка_{month_names[target_month].lower()}_{target_year}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"✓ Отчет сохранен: {output_file}")
    print("\n" + "=" * 80)
    print("Отчет успешно создан!")
    print("=" * 80)
    print(f"\nДля создания PDF:")
    print(f"1. Откройте файл в браузере (Safari или Chrome)")
    print(f"2. Нажмите Cmd+P (Печать)")
    print(f"3. Выберите 'PDF' -> 'Сохранить как PDF'")


if __name__ == "__main__":
    main()
