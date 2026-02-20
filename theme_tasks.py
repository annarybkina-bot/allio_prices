#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Группировка задач по темам на основе заголовка и описания.

На выходе формируется CSV с колонками:
- Тема (узкие, специфичные темы)
- Заголовок
- Застройщик
- Приоритет застройщика
- Приоритет от стейкхолдеров
- Дата создания
- Модуль
- Состояние пожелания
- ID задачи
"""

import csv
import re
from typing import List, Dict


INPUT_FILE = "/Users/annarybkina/Downloads/Задачи.csv"
OUTPUT_FILE = "/Users/annarybkina/Desktop/Allio/ИИ Цены/Задачи_по_темам.csv"

INPUT_FILE_2 = "/Users/annarybkina/Downloads/Задачи-2.csv"
OUTPUT_FILE_2 = "/Users/annarybkina/Desktop/Allio/ИИ Цены/Задачи-2_по_темам.csv"


def norm(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_theme(row: Dict[str, str]) -> str:
    """Определяем тему задачи по заголовку, описанию, модулю и тегам."""
    title = norm(row.get("Заголовок", ""))
    desc = norm(row.get("Описание", ""))
    module = norm(row.get("Модуль", ""))
    tags = norm(row.get("Теги", ""))
    text = " ".join([title, desc, module, tags])

    # 1. Узкие темы по фидам и агрегаторам (приоритет - проверяем сначала конкретные)
    if "авито" in text:
        return "Фиды: Авито"
    if "циан" in text or "цян" in text:
        return "Фиды: ЦИАН"
    if "домклик" in text or "дом.клик" in text:
        return "Фиды: ДомКлик"
    if "яндекс" in text and ("директ" in text or "недвижимость" in text):
        return "Фиды: Яндекс (Директ/Недвижимость)"
    if "яндекс" in text:
        return "Фиды: Яндекс"
    if "wb" in text or "wildberries" in text:
        return "Фиды: Wildberries"
    if "2гис" in text or "2gis" in text:
        return "Фиды: 2ГИС"
    if "нмаркет" in text or "nmarket" in text:
        return "Фиды: НмаркетПро"
    if "трендагент" in text or "trendagent" in text:
        return "Интеграции: ТрендАгент"
    
    # 2. Узкие темы по ПДКП/ДКП
    if "пдкп" in text:
        return "ПДКП"
    if "дкп" in text and "пдкп" not in text:
        return "ДКП"
    
    # 3. Узкие темы по EVA
    if "eva" in text or "подборщик" in text:
        if "акции" in text:
            return "EVA: Акции в каталоге"
        if "заблокирован" in text or "блокиров" in text:
            return "EVA: Фильтрация помещений"
        if "доработк" in text or "улучшен" in text:
            return "EVA: Доработки интерфейса"
        return "EVA: Общие доработки"
    
    # 4. Узкие темы по бронированию
    if "устн" in text and "брон" in text:
        if "контрол" in text or "злоупотреблен" in text:
            return "Устные брони: Контроль и ограничения"
        if "продлен" in text:
            return "Устные брони: Продление"
        if "комментар" in text:
            return "Устные брони: Комментарии"
        return "Устные брони: Общие"
    
    if "платн" in text and "брон" in text:
        if "график платежей" in text:
            return "Платные брони: График платежей"
        if "продлен" in text:
            return "Платные брони: Продление"
        if "договор" in text:
            return "Платные брони: Договоры"
        return "Платные брони: Общие"
    
    # 5. Узкие темы по фиксации
    if "фиксац" in text:
        if "агент" in text:
            return "Фиксация: Агенты"
        if "продлен" in text:
            return "Фиксация: Продление"
        if "уведомлен" in text:
            return "Фиксация: Уведомления"
        if "crm" in text or "битрикс" in text:
            return "Фиксация: Интеграция с CRM"
        return "Фиксация: Общие"
    
    # 6. Узкие темы по агентствам
    if "агентств" in module or "cashback" in module:
        if "регистрац" in text and "самозанят" in text:
            return "Агентства: Регистрация самозанятых"
        if "чат" in text:
            return "Агентства: Чат с застройщиком"
        if "бронирован" in text and "замен" in text:
            return "Агентства: Перебронирование"
        if "вознагражден" in text:
            return "Агентства: Вознаграждения"
        if "права" in text or "доступ" in text:
            return "Агентства: Права доступа"
        return "Агентства: Общие"
    
    # 7. Узкие темы по контрагентам
    if "контрагент" in module or "контрагент" in text:
        if "дубликат" in text or "дубл" in text:
            return "Контрагенты: Дубликаты"
        if "объединен" in text:
            return "Контрагенты: Объединение"
        if "паспорт" in text:
            return "Контрагенты: Паспортные данные"
        if "ип" in text or "ипо" in text:
            return "Контрагенты: ИП"
        return "Контрагенты: Общие"
    
    # 8. Узкие темы по шаблонам договоров
    if "конструктор документов" in module or "управление шаблонами" in module:
        if "дду" in text:
            return "Шаблоны: ДДУ"
        if "дкп" in text:
            return "Шаблоны: ДКП"
        if "договор бронирован" in text:
            return "Шаблоны: Договор бронирования"
        if "дополнительн" in text and "соглашен" in text:
            return "Шаблоны: Дополнительные соглашения"
        if "массов" in text and ("удален" in text or "деактив" in text):
            return "Шаблоны: Массовые операции"
        return "Шаблоны: Общие"
    
    # 9. Узкие темы по КП
    if "кп (" in module or "коммерческ" in text or "веб-кп" in text:
        if "кастомизац" in text or "персонализ" in text:
            return "КП: Кастомизация"
        if "отделка" in text:
            return "КП: Отделка"
        if "стоимость" in text or "цена" in text:
            return "КП: Стоимость и ценообразование"
        if "изображен" in text or "фото" in text:
            return "КП: Изображения"
        return "КП: Общие"
    
    # 10. Узкие темы по API и интеграциям
    if "внешнее api" in module or ("api" in text and "интеграц" in text):
        if "трендагент" in text:
            return "API: ТрендАгент"
        if "нмаркет" in text:
            return "API: НмаркетПро"
        return "API: Общие интеграции"
    
    if "интеграции crm" in module or "битрикс" in text or "b24" in text:
        if "воронк" in text:
            return "CRM: Фильтрация воронок"
        if "статус" in text and "брон" in text:
            return "CRM: Статусы брони"
        return "CRM: Общие интеграции"
    
    # 11. Узкие темы по акциям
    if "акции (" in module or "акция" in text:
        if "комбо" in text:
            return "Акции: Комбо-акции"
        if "стоимость" in text and "помещен" in text:
            return "Акции: Установка стоимости"
        if "копирован" in text:
            return "Акции: Копирование правил"
        return "Акции: Общие"
    
    # 12. Узкие темы по АЦО
    if "ацо" in text or "массовая смена цен" in module:
        if "частот" in text or "срабатыван" in text:
            return "АЦО: Частота срабатывания"
        if "уведомлен" in text:
            return "АЦО: Уведомления"
        return "АЦО: Общие"
    
    # 13. Узкие темы по графикам платежей
    if "график платежей" in text:
        if "скачиван" in text or "выгрузк" in text or "excel" in text:
            return "Графики платежей: Выгрузка"
        if "изменен" in text:
            return "Графики платежей: Изменение"
        return "Графики платежей: Общие"
    
    # 14. Узкие темы по отчетам
    if "конфигуратор отчётов" in module or "отчет" in text:
        if "выгрузк" in text or "экспорт" in text:
            return "Отчеты: Выгрузка"
        if "контрагент" in text:
            return "Отчеты: По контрагентам"
        if "брон" in text:
            return "Отчеты: По броням"
        return "Отчеты: Общие"
    
    # 15. Узкие темы по шахматке
    if "шахматк" in module or "шахматк" in text:
        if "статус" in text:
            return "Шахматка: Статусы"
        if "перспектив" in text:
            return "Шахматка: Перспектива"
        if "цвет" in text or "легенд" in text:
            return "Шахматка: Визуализация"
        return "Шахматка: Общие"
    
    # 16. Узкие темы по массовому редактору
    if "массовый редактор" in module:
        if "пиб" in text:
            return "Массовый редактор: ПИБ"
        if "описан" in text:
            return "Массовый редактор: Описания"
        return "Массовый редактор: Общие"
    
    # 17. Узкие темы по карточкам сделок
    if "карточки сделок" in module:
        if "график платежей" in text:
            return "Карточка сделки: График платежей"
        if "эскроу" in text:
            return "Карточка сделки: Эскроу-счета"
        if "дополнительн" in text and "соглашен" in text:
            return "Карточка сделки: Доп. соглашения"
        return "Карточка сделки: Общие"
    
    # 18. Узкие темы по правам доступа
    if "права (" in module or "доступ" in text:
        if "объект" in text:
            return "Права: Доступ к объектам"
        if "офис" in text:
            return "Права: Доступ по офисам"
        if "реестр" in text:
            return "Права: Доступ к реестрам"
        if "пожелан" in text:
            return "Права: Пожелания застройщика"
        return "Права: Общие"
    
    # 19. Узкие темы по уведомлениям
    if "уведомлен" in module or "уведомлен" in text:
        if "telegram" in text or "тг" in text:
            return "Уведомления: Telegram"
        if "ассистент" in text:
            return "Уведомления: Ассистент"
        return "Уведомления: Общие"
    
    # 20. Узкие темы по ПИБ
    if "пиб" in text:
        if "замен" in text:
            return "ПИБ: Замена площадей"
        if "массов" in text:
            return "ПИБ: Массовое заполнение"
        return "ПИБ: Общие"
    
    # 21. Узкие темы по личному кабинету
    if "личный кабинет" in text or "лк " in text:
        if "блок" in text:
            return "ЛК: Новые блоки"
        if "создан" in text:
            return "ЛК: Создание ЛК"
        return "ЛК: Общие"
    
    # 22. Узкие темы по галерее
    if "галере" in text or "galere" in text:
        if "порядок" in text or "корпус" in text:
            return "Галерея: Порядок корпусов"
        return "Галерея: Общие"
    
    # 23. Узкие темы по заявкам на договор
    if "заявки на договор" in module:
        if "согласован" in text:
            return "Заявки на договор: Согласование"
        if "уведомлен" in text:
            return "Заявки на договор: Уведомления"
        return "Заявки на договор: Общие"
    
    # 24. Фолбэк - общие темы
    if "брон" in text:
        return "Бронирование: Прочее"
    if "договор" in text:
        return "Договоры: Прочее"
    if "отчет" in text or "отчёт" in text:
        return "Отчеты: Прочее"
    
    return "Прочее"


def process_file(input_file: str, output_file: str) -> None:
    """Обрабатывает один файл и создает выходной CSV с темами."""
    with open(input_file, "r", encoding="utf-8-sig") as f:  # utf-8-sig убирает BOM
        reader = csv.DictReader(f)
        rows: List[Dict[str, str]] = list(reader)

    themed_rows = []
    for row in rows:
        # Нормализуем ключи - убираем кавычки и BOM
        normalized_row = {}
        for key, value in row.items():
            # Убираем BOM, кавычки и лишние пробелы из ключей
            clean_key = key.strip().strip('"').strip('\ufeff').strip()
            normalized_row[clean_key] = value
        
        theme = detect_theme(normalized_row)
        
        # Получаем ID задачи - пробуем разные варианты названия
        task_id = ""
        for key in row.keys():
            if "ID задачи" in key or "id задачи" in key.lower():
                task_id = row[key].strip().strip('"')
                break
        
        # Получаем состояние пожелания
        wish_state = normalized_row.get("Состояние пожелания", "").strip().strip('"')
        
        themed_rows.append(
            {
                "Тема": theme,
                "Заголовок": normalized_row.get("Заголовок", "").strip().strip('"'),
                "Застройщик": normalized_row.get("Застройщик", "").strip().strip('"'),
                "Приоритет застройщика": normalized_row.get("Приоритет застройщика", "").strip().strip('"'),
                "Приоритет от стейкхолдеров": normalized_row.get("Приоритет от стейкхолдеров", "").strip().strip('"'),
                "Дата создания": normalized_row.get("Создана", "").strip().strip('"'),
                "Модуль": normalized_row.get("Модуль", "").strip().strip('"'),
                "Состояние пожелания": wish_state,
                "ID задачи": task_id,
            }
        )

    # Сортируем: сначала по теме, внутри — по дате создания (как строка, здесь это достаточно)
    themed_rows.sort(key=lambda r: (r["Тема"], r["Дата создания"]))

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Тема",
                "Заголовок",
                "Застройщик",
                "Приоритет застройщика",
                "Приоритет от стейкхолдеров",
                "Дата создания",
                "Модуль",
                "Состояние пожелания",
                "ID задачи",
            ],
        )
        writer.writeheader()
        writer.writerows(themed_rows)

    print(f"Сгруппированные по темам задачи сохранены в: {output_file}")


def main() -> None:
    # Обрабатываем первый файл
    process_file(INPUT_FILE, OUTPUT_FILE)
    
    # Обрабатываем второй файл
    import os
    if os.path.exists(INPUT_FILE_2):
        process_file(INPUT_FILE_2, OUTPUT_FILE_2)
    else:
        print(f"Файл {INPUT_FILE_2} не найден")


if __name__ == "__main__":
    main()

