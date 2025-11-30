from typing import Dict, Iterable, List, Tuple, Union
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

    Поддерживает два сценария:
    1. Старый паттерн: элементы с классами 'problem-header' и 'problem-body'
    2. Новый паттерн: qblock-и с и без ID, где qblock без ID - общий контекст
    """
    if isinstance(dom_or_html, str):
        dom = extract_dom_tree(dom_or_html)
    else:
        dom = dom_or_html

    # Попробуем сначала старый паттерн
    pairs = _extract_block_pairs_by_header_body_pattern(dom)

    # Если не нашли ничего по старому паттерну, используем новый
    if not pairs:
        pairs = _extract_block_pairs_by_qblocks_pattern_with_grouping(dom)

    return pairs


def _extract_block_pairs_by_header_body_pattern(dom: BeautifulSoup) -> List[Tuple[str, str]]:
    """
    Старая логика: ищет элементы с классами 'problem-header' и 'problem-body'.
    """
    pairs: List[Tuple[str, str]] = []

    # Простая и надёжная эвристика: пара — это элемент с классом "problem-header"
    # и ближайший следующий sibling с классом "problem-body" (или похожие варианты).
    headers = _find_header_elements(dom)

    for header in headers:
        body = _find_body_element_for_header(header)
        header_html = str(header)
        body_html = str(body) if body is not None else ""
        pairs.append((header_html, body_html))

    return pairs


def _find_header_elements(dom: BeautifulSoup) -> List[Tag]:
    """
    Находит элементы, которые могут быть заголовками задач.
    """
    # Основной паттерн: элементы с классом "problem-header"
    headers = dom.find_all(class_="problem-header")
    if not headers:
        # fallback: элементы с тегами h2, h3 и классом, содержащим "task"
        headers = dom.find_all(lambda el: el.name in ("h3", "h2") and "task" in (el.get("class") or []))
    return headers


def _find_next_tag_sibling(tag: Tag) -> Tag | None:
    """Вспомогательная функция: находит ближайший следующий HTML-элемент (Tag), пропуская NavigableString и комментарии."""
    sib = tag.next_sibling
    while sib and not isinstance(sib, Tag):
        sib = sib.next_sibling
    return sib


def _find_body_element_for_header(header: Tag) -> Tag | None:
    """
    Находит элемент, который может быть телом задачи для заданного заголовка.
    Использует две последовательные, упрощенные стратегии поиска.
    """
    # СТРАТЕГИЯ 1: Поиск ближайшего следующего sibling, который является телом
    sib = _find_next_tag_sibling(header)
    while sib:
        if sib.name == "div" or "problem-body" in (sib.get("class") or []):
            return sib

        # Останавливаем поиск по sibling, если встречаем новый заголовок,
        # чтобы не "перепрыгнуть" в следующую задачу
        if "problem-header" in (sib.get("class") or []):
            break 

        sib = _find_next_tag_sibling(sib)

    # СТРАТЕГИЯ 2: Поиск внутри родительского контейнера (резервный вариант)
    if header.parent:
        possible = header.parent.find_all(class_="problem-body")
        if possible:
            return possible[0]

    return None


def _extract_block_pairs_by_qblocks_pattern_with_grouping(dom: BeautifulSoup) -> List[Tuple[str, str]]:
    """
    Новая логика: Обработка qblock-ов как на страницах ФИПИ с учетом группировки.
    Общий qblock без ID (или ID не начинается с 'q') может содержать общий контекст
    для следующих за ним qblock-ов с ID, до следующего общего qblock-а или до конца.
    Возвращает пары (header, body), где body может содержать несколько qblock-ов с общим контекстом.
    """
    pairs: List[Tuple[str, str]] = []
    qblocks = dom.find_all(class_='qblock')

    # Группируем qblock-и: сначала общий контекст (если есть), потом список индивидуальных qblock-ов
    groups = _group_qblocks_by_context(qblocks)

    for group in groups:
        common_context = group['common_context']
        individual_qblocks = group['individual_qblocks']

        if not individual_qblocks:
            # Если в группе нет индивидуальных qblock-ов, пропускаем её
            continue

        if common_context:
            # Если есть общий контекст, объединяем все индивидуальные qblock-и в одну задачу
            # Header: используем ID первого qblock в группе или генерируем общий
            first_qblock_id = individual_qblocks[0].get('id', '')[1:] if individual_qblocks else 'group'
            header_html = f'<div id="i{first_qblock_id}" class="header-container">Задание {first_qblock_id}</div>'

            # Body: объединяем общий контекст и все индивидуальные qblock-и
            body_parts = [common_context] + [str(qb) for qb in individual_qblocks]
            body_html = ''.join(body_parts)

            pairs.append((header_html, body_html))
        else:
            # Если нет общего контекста, создаем отдельные пары для каждого индивидуального qblock
            for qblock in individual_qblocks:
                qblock_id = qblock.get('id', '')[1:]  # Убираем 'q' префикс
                header_html = f'<div id="i{qblock_id}" class="header-container">Задание {qblock_id}</div>'
                body_html = str(qblock)

                pairs.append((header_html, body_html))

    return pairs


def _group_qblocks_by_context(qblocks: List[Tag]) -> List[Dict]:
    """
    Группирует qblock-и по общему контексту.

    Args:
        qblocks: Список BeautifulSoup Tag объектов с классом 'qblock'

    Returns:
        Список словарей, где каждый словарь содержит:
        - 'common_context': HTML-строка общего контекста (или None)
        - 'individual_qblocks': Список BeautifulSoup Tag объектов индивидуальных qblock-ов
    """
    groups = []
    current_group = {'common_context': None, 'individual_qblocks': []}

    for qblock in qblocks:
        qblock_id = qblock.get('id', '')

        if not qblock_id or not qblock_id.startswith('q'):
            # Это общий контекст
            # Если в текущей группе уже есть индивидуальные qblock-и, 
            # завершаем её и начинаем новую
            if current_group['individual_qblocks']:
                groups.append(current_group)
                current_group = {'common_context': None, 'individual_qblocks': []}

            # Устанавливаем общий контекст для новой группы
            current_group['common_context'] = str(qblock)
        else:
            # Это индивидуальный qblock
            current_group['individual_qblocks'].append(qblock)

    # Добавляем последнюю группу, если она не пуста
    if current_group['individual_qblocks'] or current_group['common_context']:
        groups.append(current_group)

    return groups


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
