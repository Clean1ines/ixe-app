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
    Подход: ищем элементы, которые в текущем коде используются как header/qblock.
    Это удобно тестировать: вход — строка, выход — список кортежей строк.
    Возвращаем HTML-представление элементов (str), чтобы дальнейшие pure-функции
    могли оперировать текстом, не завися от BS-объектов.
    """
    if isinstance(dom_or_html, str):
        dom = extract_dom_tree(dom_or_html)
    else:
        dom = dom_or_html

    pairs: List[Tuple[str, str]] = []

    # Простая и надёжная эвристика: пара — это элемент с классом "problem-header"
    # и ближайший следующий sibling с классом "problem-body" (или похожие варианты).
    # Это место, которое ты потом можешь подстроить под реальные селекторы FIPI.
    headers = dom.find_all(class_="problem-header")
    if not headers:
        # fallback: используем контейнеры с data-task-id или заголовки h3 + div
        headers = dom.find_all(lambda el: el.name in ("h3", "h2") and "task" in (el.get("class") or []))

    for header in headers:
        # ищем ближайший элемент после header, который выглядит как тело блока
        # допустим, это следующий sibbling div
        body = None
        sib = header.find_next_sibling()
        while sib and (not (isinstance(sib, Tag))):
            sib = sib.find_next_sibling() if hasattr(sib, "find_next_sibling") else None
        # Проверяем несколько вариантов, остановимся на первом диве
        while sib and isinstance(sib, Tag) and body is None:
            if sib.name == "div" or "problem-body" in (sib.get("class") or []):
                body = sib
                break
            sib = sib.find_next_sibling()
        # Если не нашли, попробуем поиск внутри общего контейнера
        if body is None:
            possible = header.parent.find_all(class_="problem-body") if header.parent else []
            body = possible[0] if possible else None

        header_html = str(header)
        body_html = str(body) if body is not None else ""
        pairs.append((header_html, body_html))

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
