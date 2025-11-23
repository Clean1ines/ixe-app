from typing import List, Tuple, Dict, Iterable, Union
from pathlib import Path
from bs4 import BeautifulSoup, Tag

"""
Чистые функции для разбора HTML и подготовки "сырых" данных.
Правило: функции не должны выполнять I/O (нет сетевых вызовов, файлов), они принимают
строки или DOM и возвращают простые структуры данных (list/dict).
Это — функциональное ядро (Functional Core).
"""

def extract_dom_tree(html: str) -> BeautifulSoup:
    """
    Преобразует HTML-строку в BeautifulSoup DOM. Чистая функция:
    deterministic, не делает I/O.
    """
    return BeautifulSoup(html or "", "html.parser")


def extract_block_pairs(dom_or_html: Union[str, BeautifulSoup]) -> List[Tuple[str, str]]:
    """
    Из DOM (или HTML-строки) извлекает упорядоченный список пар (header_html, body_html).
    
    НОВАЯ ЛОГИКА:
    - Ищем элементы с классом 'qblock'
    - Если qblock не имеет ID (или ID начинается не с 'q'), считаем его общим контекстом
    - Если qblock имеет ID, начинающийся с 'q', считаем его индивидуальным заданием
    - Для индивидуальных заданий: header - это div с id="i<ID>" (где ID из qblock), body - сам qblock
    - Общие контексты прикрепляются к следующему индивидуальному заданию (если применимо)
    """
    if isinstance(dom_or_html, str):
        dom = extract_dom_tree(dom_or_html)
    else:
        dom = dom_or_html

    pairs: List[Tuple[str, str]] = []
    qblocks = dom.find_all(class_='qblock')
    
    common_context = None
    
    for qblock in qblocks:
        qblock_id = qblock.get('id', '')
        
        # Проверяем, является ли это общим qblock-ом (без ID или ID не начинается с 'q')
        if not qblock_id or not qblock_id.startswith('q'):
            # Сохраняем общий контекст
            common_context = str(qblock)
            continue
        
        # Это индивидуальное задание (ID начинается с 'q')
        # Создаем header с id="i<ID>"
        task_id = qblock_id[1:]  # Убираем 'q' префикс
        header_html = f'<div id="i{task_id}" class="header-container">Задание {task_id}</div>'
        
        # Создаем body, объединяя общий контекст (если есть) с индивидуальным qblock
        individual_qblock_html = str(qblock)
        
        if common_context:
            # Вставляем общий контекст в начало индивидуального qblock
            # Это грубое объединение, в реальности может потребоваться более точное вмешательство в DOM
            body_html = f"{common_context}{individual_qblock_html}"
        else:
            body_html = individual_qblock_html
            
        pairs.append((header_html, body_html))
        
        # Сбрасываем общий контекст после использования (он может применяться только к следующему заданию)
        # В реальности логика может быть сложнее: общий контекст может применяться к нескольким заданиям
        # или до следующего общего контекста. Для упрощения сбрасываем после первого использования.
        common_context = None

    return pairs


def transform_blocks_to_raw_data(block_pairs: Iterable[Tuple[str, str]]) -> List[Dict]:
    """
    Преобразует пары (header_html, body_html) в список "сырых" dict-объектов,
    пригодных для feed в фабрику Problem или для дальнейшей обработки.
    Здесь извлекаем базовые поля: header_html, body_html, maybe id/title.
    Функция остаётся чистой.
    """
    raw = []
    for header_html, body_html in block_pairs:
        # минимальная постобработка: можно извлечь номер задачи, id, хэши и т.д.
        # Для безопасности парсим header_html как DOM, но не делаем I/O.
        header_dom = BeautifulSoup(header_html, "html.parser")
        # Попытаемся извлечь атрибут data-task-id или цифры в заголовке
        task_id = header_dom.find(attrs={"data-task-id": True})
        task_id_val = task_id.get("data-task-id") if task_id else None

        # Попробуем взять текст заголовка
        title = header_dom.get_text(strip=True)[:200] if header_dom else None

        raw_item = {
            "header_html": header_html,
            "body_html": body_html,
            "task_id": task_id_val,
            "title": title,
        }
        raw.append(raw_item)
    return raw
