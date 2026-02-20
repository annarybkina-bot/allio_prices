#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обработки задач техподдержки:
- Поиск дубликатов по заголовку и описанию
- Объединение дубликатов в темы
- Формирование итоговой таблицы
"""

import csv
import re
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher

def normalize_text(text):
    """Нормализация текста для сравнения"""
    if not text:
        return ""
    # Приводим к нижнему регистру
    text = text.lower()
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем знаки препинания в конце (точки, запятые и т.д.)
    text = re.sub(r'[.,;:!?]+$', '', text)
    # Удаляем двойные кавычки
    text = text.replace('"', '').replace('«', '').replace('»', '')
    # Удаляем лишние пробелы снова после удаления знаков
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def similarity(text1, text2):
    """Вычисление схожести двух текстов"""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()

def parse_date(date_str):
    """Парсинг даты из формата CSV"""
    if not date_str or date_str == "":
        return None
    try:
        # Формат: "3 дек. 2025 15:24"
        months = {
            'янв': '01', 'февр': '02', 'мар': '03', 'апр': '04',
            'май': '05', 'июн': '06', 'июл': '07', 'авг': '08',
            'сент': '09', 'окт': '10', 'нояб': '11', 'дек': '12'
        }
        parts = date_str.split()
        if len(parts) >= 3:
            day = parts[0]
            month_name = parts[1].rstrip('.')
            year = parts[2]
            month = months.get(month_name[:4], '01')
            return f"{year}-{month}-{day.zfill(2)}"
    except:
        pass
    return date_str

def read_csv_file(filepath):
    """Чтение CSV файла"""
    tasks = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    return tasks

def find_duplicates(tasks, title_threshold=0.70, description_threshold=0.5):
    """Поиск дубликатов задач"""
    n = len(tasks)
    # Массив для отслеживания, к какой группе принадлежит задача
    group_id = list(range(n))
    
    def find_group(x):
        """Поиск корня группы (Union-Find)"""
        if group_id[x] != x:
            group_id[x] = find_group(group_id[x])
        return group_id[x]
    
    def union(x, y):
        """Объединение двух групп"""
        root_x = find_group(x)
        root_y = find_group(y)
        if root_x != root_y:
            group_id[root_y] = root_x
    
    # Нормализуем все заголовки и описания заранее
    normalized_data = []
    for task in tasks:
        title = normalize_text(task.get('Заголовок', ''))
        desc = normalize_text(task.get('Описание', ''))
        normalized_data.append((title, desc))
    
    # Сравниваем каждую пару задач
    print("  Сравнение задач...")
    comparisons = 0
    for i in range(n):
        if i % 50 == 0:
            print(f"    Обработано {i}/{n} задач...")
        
        title1, desc1 = normalized_data[i]
        if not title1:
            continue
        
        for j in range(i + 1, n):
            title2, desc2 = normalized_data[j]
            if not title2:
                continue
            
            comparisons += 1
            
            # Проверяем схожесть заголовков
            title_sim = similarity(title1, title2)
            
            # Проверяем, является ли один заголовок подстрокой другого
            # (для случаев типа "Добавить настройку..." и "Добавить настройку... в Галерее")
            is_substring = False
            if len(title1) > 20 and len(title2) > 20:  # Только для достаточно длинных заголовков
                shorter = title1 if len(title1) < len(title2) else title2
                longer = title1 if len(title1) >= len(title2) else title2
                # Если более короткий заголовок составляет большую часть длинного
                if shorter in longer or longer.startswith(shorter[:int(len(shorter) * 0.8)]):
                    is_substring = True
            
            # Если заголовки очень похожи (высокий порог) или один является подстрокой другого
            if title_sim >= 0.9 or is_substring:
                union(i, j)
            # Если заголовки похожи (средний порог) и есть описание
            elif title_sim >= title_threshold:
                # Проверяем описание, если оно есть
                if desc1 and desc2:
                    desc_sim = similarity(desc1, desc2)
                    # Если и заголовки, и описания похожи
                    if desc_sim >= description_threshold:
                        union(i, j)
                # Если описания нет, но заголовки очень похожи
                elif title_sim >= 0.80:
                    union(i, j)
    
    print(f"  Всего сравнений: {comparisons}")
    
    # Группируем задачи по их корневым группам
    groups_dict = defaultdict(list)
    for i in range(n):
        root = find_group(i)
        groups_dict[root].append(i)
    
    groups = list(groups_dict.values())
    
    return groups

def merge_group_info(tasks, group_indices):
    """Объединение информации из группы задач"""
    group_tasks = [tasks[i] for i in group_indices]
    
    # Выбираем наиболее полный заголовок
    titles = [t.get('Заголовок', '').strip() for t in group_tasks if t.get('Заголовок', '').strip()]
    title = max(titles, key=len) if titles else ""
    
    # Объединяем застройщиков (уникальные значения)
    developers = set()
    for t in group_tasks:
        dev = t.get('Застройщик', '').strip()
        if dev and dev != 'Нет: застройщик':
            developers.add(dev)
    developer = ', '.join(sorted(developers)) if developers else ""
    
    # Приоритеты - берем наивысший (A > B > C)
    priority_map = {'A': 3, 'B': 2, 'C': 1, '': 0}
    
    dev_priorities = []
    stake_priorities = []
    
    for t in group_tasks:
        dev_pri = t.get('Приоритет застройщика', '').strip()
        stake_pri = t.get('Приоритет от стейкхолдеров', '').strip()
        
        if dev_pri and dev_pri not in ['Нет: приоритет застройщика', '']:
            dev_priorities.append(dev_pri)
        if stake_pri and stake_pri not in ['Нет: приоритет от стейкхолдера', '']:
            stake_priorities.append(stake_pri)
    
    # Выбираем наивысший приоритет
    dev_priority = max(dev_priorities, key=lambda x: priority_map.get(x, 0)) if dev_priorities else ""
    stake_priority = max(stake_priorities, key=lambda x: priority_map.get(x, 0)) if stake_priorities else ""
    
    # Дата создания - берем самую раннюю
    dates = []
    for t in group_tasks:
        date_str = t.get('Создана', '').strip()
        if date_str:
            parsed = parse_date(date_str)
            if parsed:
                dates.append((parsed, date_str))
    
    creation_date = min(dates, key=lambda x: x[0])[1] if dates else ""
    
    return {
        'title': title,
        'developer': developer,
        'dev_priority': dev_priority,
        'stake_priority': stake_priority,
        'creation_date': creation_date,
        'task_ids': [tasks[i].get('ID задачи', '') for i in group_indices]
    }

def main():
    input_file = '/Users/annarybkina/Downloads/Задачи.csv'
    output_file = '/Users/annarybkina/Desktop/Allio/ИИ Цены/Объединенные_задачи.md'
    
    print("Чтение CSV файла...")
    tasks = read_csv_file(input_file)
    print(f"Прочитано задач: {len(tasks)}")
    
    print("Поиск дубликатов...")
    groups = find_duplicates(tasks)
    print(f"Найдено групп: {len(groups)}")
    
    print("Объединение информации...")
    merged_topics = []
    for i, group in enumerate(groups):
        if len(group) > 1:
            print(f"  Группа {i+1}: {len(group)} задач объединены")
        info = merge_group_info(tasks, group)
        merged_topics.append(info)
    
    # Сортируем по дате создания (самые старые первые)
    merged_topics.sort(key=lambda x: parse_date(x['creation_date']) or '9999-99-99')
    
    print(f"\nСоздание итоговой таблицы...")
    
    # Формируем Markdown таблицу
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Объединенные задачи техподдержки\n\n")
        f.write(f"Всего задач: {len(tasks)}\n")
        f.write(f"Объединено в тем: {len(merged_topics)}\n")
        f.write(f"Дубликатов найдено: {sum(1 for g in groups if len(g) > 1)}\n\n")
        
        f.write("| № | Заголовок | Застройщик | Приоритет застройщика | Приоритет от стейка | Дата создания | ID задач |\n")
        f.write("|:-:|:----------|:-----------|:---------------------|:-------------------|:--------------|:----------|\n")
        
        for i, topic in enumerate(merged_topics, 1):
            title = topic['title'].replace('|', '\\|')
            developer = topic['developer'].replace('|', '\\|')
            dev_pri = topic['dev_priority'] or '-'
            stake_pri = topic['stake_priority'] or '-'
            date = topic['creation_date'] or '-'
            task_ids = ', '.join(topic['task_ids'])
            
            f.write(f"| {i} | {title} | {developer} | {dev_pri} | {stake_pri} | {date} | {task_ids} |\n")
    
    print(f"\nРезультат сохранен в: {output_file}")
    
    # Также создаем CSV версию
    csv_output = '/Users/annarybkina/Desktop/Allio/ИИ Цены/Объединенные_задачи.csv'
    with open(csv_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['№', 'Заголовок', 'Застройщик', 'Приоритет застройщика', 
                        'Приоритет от стейка', 'Дата создания', 'ID задач'])
        for i, topic in enumerate(merged_topics, 1):
            writer.writerow([
                i,
                topic['title'],
                topic['developer'],
                topic['dev_priority'] or '',
                topic['stake_priority'] or '',
                topic['creation_date'] or '',
                ', '.join(topic['task_ids'])
            ])
    
    print(f"CSV версия сохранена в: {csv_output}")

if __name__ == '__main__':
    main()
