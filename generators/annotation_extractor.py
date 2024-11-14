import os
import fitz  
import json
from PIL import Image, ImageDraw, ImageFont
import re

VISUALISE = True
PDF_DIR = './data/pdf'
IMAGE_DIR = './data/image'
VISUAL_DIR = './data/visualizations'
JSON_DIR = './data/json'

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VISUAL_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

FONT_PATH = "arial.ttf"
FONT_SIZE = 16

def check_overlap(bbox1, bbox2, threshold=0.1):
    """
    Проверка перекрытия блоков с порогом.
    Порог — это минимальная доля пересечения по меньшей площади из двух блоков.
    """
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2

    # находим пересечение
    x_left = max(x1_min, x2_min)
    y_top = max(y1_min, y2_min)
    x_right = min(x1_max, x2_max)
    y_bottom = min(y1_max, y2_max)

    if x_right < x_left or y_bottom < y_top:
        return False  # нет пересечения

    # вычисляем площади пересечения и меньшей области
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
    bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)
    min_area = min(bbox1_area, bbox2_area)

    # проверяем относительное перекрытие с заданным порогом
    overlap_ratio = intersection_area / min_area
    return overlap_ratio > threshold

def are_bboxes_close(bbox1, bbox2, threshold_x=5, threshold_y=2, overlap_threshold=0.0001):
    """Проверяет, находятся ли два bbox достаточно близко друг к другу."""
    
    # распаковка координат
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2
    
    # проверка близости по горизонтали
    def check_horizontal_proximity():
        # если один bbox справа от другого
        if x0_1 > x1_2:
            return (x0_1 - x1_2) < threshold_x
        if x0_2 > x1_1:
            return (x0_2 - x1_1) < threshold_x
        return True
    
    # проверка близости по вертикали
    def check_vertical_proximity():
        # если один bbox выше другого
        if y0_1 > y1_2:
            return (y0_1 - y1_2) < threshold_y
        if y0_2 > y1_1:
            return (y0_2 - y1_1) < threshold_y
        return True
    
    # bbox считаются близкими если они либо перекрываются,
    # либо находятся достаточно близко друг к другу по обеим осям
    return check_overlap(bbox1, bbox2, threshold=overlap_threshold) or (check_horizontal_proximity() and check_vertical_proximity())

def visualize_elements(image_path, elements, output_path, page_width, page_height):
    # создаем новое изображение с размерами страницы
    img = Image.new("RGBA", (page_width, page_height), (255, 255, 255, 0))
    
    # открываем исходное изображение и масштабируем его до размеров страницы
    background = Image.open(image_path).convert("RGBA")
    background = background.resize((page_width, page_height))
    
    # накладываем исходное изображение на прозрачный фон
    img.paste(background, (0, 0))
    
    draw = ImageDraw.Draw(img, "RGBA")
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        font = ImageFont.load_default()
        
    color_map = {
        "title": (255, 0, 0, 80),
        "paragraph": (0, 255, 0, 80),
        "table": (0, 0, 255, 80),
        "picture": (255, 255, 0, 80),
        "table_signature": (255, 0, 255, 80),
        "picture_signature": (0, 255, 255, 80),
        "numbered_list": (128, 0, 128, 80),
        "marked_list": (128, 128, 0, 80),
        "header": (0, 128, 128, 80),
        "footer": (128, 0, 0, 80),
        "footnote": (0, 128, 0, 80),
        "formula": (0, 0, 128, 80)
    }

    # масштабируем координаты в соответствии с размерами страницы
    def scale_coordinates(coords, orig_width, orig_height):
        x0, y0, x1, y1 = coords
        scale_x = page_width / orig_width
        scale_y = page_height / orig_height
        return [
            int(x0 * scale_x),
            int(y0 * scale_y),
            int(x1 * scale_x),
            int(y1 * scale_y)
        ]

    for key, boxes in elements.items():
        if key in ["image_path", "image_height", "image_width"]:
            continue
            
        orig_width = elements.get("image_width", page_width)
        orig_height = elements.get("image_height", page_height)

        for box in boxes:
            if not isinstance(box, list) or len(box) != 4:
                continue

            # масштабируем координаты
            scaled_box = scale_coordinates(box, orig_width, orig_height)
            x0, y0, x1, y1 = scaled_box
            
            color = color_map.get(key, (255, 255, 255, 80))
            
            # создаем отдельный слой для каждого прямоугольника
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # рисуем прямоугольник на отдельном слое
            overlay_draw.rectangle([x0, y0, x1, y1], fill=color, outline=(0, 0, 0, 255))
            
            # накладываем слой на основное изображение
            img = Image.alpha_composite(img, overlay)
            
            # добавляем текст
            draw = ImageDraw.Draw(img)
            text_color = (0, 0, 0, 255)  # черный цвет для текста
            draw.text((x0 + 5, y0 + 5), key, fill=text_color, font=font)

    img.save(output_path)

def is_inside(box1, box2, tolerance=0):
        """Проверяет, находится ли box1 внутри box2 с учетом погрешности."""
        return (box1[0] >= box2[0] - tolerance and box1[1] >= box2[1] - tolerance and 
                box1[2] <= box2[2] + tolerance and box1[3] <= box2[3] + tolerance)

def merge_boxes(box1, box2):
    """Объединяет два бокса"""
    return [
        min(box1[0], box2[0]),  # x0
        min(box1[1], box2[1]),  # y0
        max(box1[2], box2[2]),  # x1
        max(box1[3], box2[3])   # y1
    ]

def do_overlap(box1, box2):
        """Проверяет, пересекаются ли боксы"""
        return not (box1[2] <= box2[0] or  # box1 слева от box2
                   box1[0] >= box2[2] or   # box1 справа от box2
                   box1[3] <= box2[1] or   # box1 выше box2
                   box1[1] >= box2[3])     # box1 ниже box2

def merge_blocks(elements):
    """Объединяет блоки одного типа"""

    if not isinstance(elements, dict):
        raise TypeError('elements должен быть словарём')

    def is_vertically_close(box1, box2, max_gap=15):
        """Проверяет, находятся ли боксы достаточно близко по вертикали"""
        vertical_gap = abs(box1[3] - box2[1]) if box1[3] < box2[1] else abs(box2[3] - box1[1])
        horizontal_overlap = not (box1[2] < box2[0] or box1[0] > box2[2])
        return vertical_gap <= max_gap and horizontal_overlap

    def is_horizontally_close(box1, box2, type_of_block, max_gap=5):
        """Проверяет, находятся ли боксы достаточно близко по горизонтали"""
        if type_of_block == 'marked_list' or type_of_block == 'numbered_list':
            max_gap = 30
        horizontal_gap = abs(box1[2] - box2[0]) if box1[2] < box2[0] else abs(box2[2] - box1[0])
        vertical_overlap = not (box1[3] < box2[1] or box1[1] > box2[3])
        return horizontal_gap <= max_gap and vertical_overlap

    def process_column_blocks(blocks_in_column):
        """Обрабатывает блоки внутри одной колонки"""
        if not blocks_in_column:
            return []
            
        # сортируем блоки в колонке по вертикали, затем по горизонтали
        blocks_in_column.sort(key=lambda x: (x['coords'][1], x['coords'][0]))
        
        i = 0
        while i < len(blocks_in_column):
            j = i + 1
            while j < len(blocks_in_column):
                if blocks_in_column[i]['type'] == blocks_in_column[j]['type']:
                    type_of_block = blocks_in_column[i]['type']

                    box1 = blocks_in_column[i]['coords']
                    box2 = blocks_in_column[j]['coords']
                    
                    # Проверяем блоки между ними
                    blocks_between = blocks_in_column[i+1:j]
                    has_other_blocks_between = any(
                        b['type'] != blocks_in_column[i]['type'] 
                        for b in blocks_between
                    )
                    
                    should_merge = False
                    if not has_other_blocks_between:
                        if is_inside(box1, box2) or is_inside(box2, box1):
                            should_merge = True
                        elif do_overlap(box1, box2):
                            should_merge = True
                        elif is_vertically_close(box1, box2):
                            should_merge = True
                        elif is_horizontally_close(box1, box2, type_of_block):
                            should_merge = True
                    
                    if should_merge:
                        merged_box = merge_boxes(box1, box2)
                        blocks_in_column[i]['coords'] = merged_box
                        blocks_in_column.pop(j)
                        continue
                j += 1
            i += 1
        
        return blocks_in_column
    
    # создаем список всех блоков
    all_blocks = []
    for block_type, blocks in elements.items():
        if block_type not in ["multicolumn_2", "multicolumn_3"]:
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, (list, tuple)) and len(block) == 4:
                        all_blocks.append({
                            'type': block_type,
                            'coords': list(block)
                        })

    # если нет блоков для обработки, возвращаем исходный словарь
    if not all_blocks:
        return elements

    processed_blocks = []
    
    # обрабатываем оставшиеся блоки
    remaining_blocks = [block for block in all_blocks]
    processed_blocks.extend(process_column_blocks(remaining_blocks))
    
    result = {}
    
    for key in ["image_path", "image_height", "image_width"]:
        if key in elements:
            result[key] = elements[key]
    
    # группируем обработанные блоки по типам
    for block_type in elements:
        if block_type not in ["image_path", "image_height", "image_width"]:
            result[block_type] = []
    
    # заполняем результат обработанными блоками
    for block in processed_blocks:
        if block['type'] in result:
            result[block['type']].append(block['coords'])

    # ещё раз отдельно пройдём по формулам и склеим их, где надо
    if result['formula']:
        
        k = len(result['formula'])
        for _ in range(min(k, 4)):
            result_formula_len = len(result['formula'])
            new_result = result.copy()
            new_result['formula'] = []
            used_indices = set()  # отслеживаем использованные индексы
            
            for i in range(result_formula_len):
                if i in used_indices:  # пропускаем уже использованные элементы
                    continue
                    
                was_merged = False
                bbox1 = result['formula'][i]
                
                for j in range(i + 1, result_formula_len):
                    if j in used_indices:  # пропускаем уже использованные элементы
                        continue
                        
                    bbox2 = result['formula'][j]
                    if are_bboxes_close(bbox1, bbox2):
                        new_result['formula'].append(merge_boxes(bbox1, bbox2))
                        used_indices.add(i)
                        used_indices.add(j)
                        was_merged = True
                        break
                        
                if not was_merged and i not in used_indices:
                    new_result['formula'].append(bbox1)
                    
            # добавляем оставшиеся неиспользованные элементы
            for i in range(result_formula_len):
                if i not in used_indices:
                    new_result['formula'].append(result['formula'][i])
                    
            result = new_result.copy()
        new_result = result.copy()
        result['formula'] = []
        for bbox in new_result['formula']:
            if not (bbox in result['formula']):
                result['formula'].append(bbox)
        
        new_result = result.copy()
        new_result['formula'] = []
        for i in range(len(result['formula'])):
            bbox1 = result['formula'][i]
            to_check = result['formula'][:i] + result['formula'][i+1:]
            if not any(is_inside(bbox1, bbox2) for bbox2 in to_check):
                new_result['formula'].append(bbox1)
        result = new_result.copy()

    # ещё раз отдельно пройдём по paragraph'ам и тоже досклеим их
    if result['paragraph']:
        
        k = len(result['paragraph'])
        for _ in range(2):
            result_paragraph_len = len(result['paragraph'])
            new_result = result.copy()
            new_result['paragraph'] = []
            used_indices = set()  # отслеживаем использованные индексы
            
            for i in range(result_paragraph_len):
                if i in used_indices:  # пропускаем уже использованные элементы
                    continue
                    
                was_merged = False
                bbox1 = result['paragraph'][i]
                
                for j in range(i + 1, result_paragraph_len):
                    if j in used_indices:  # пропускаем уже использованные элементы
                        continue
                        
                    bbox2 = result['paragraph'][j]
                    if do_overlap(bbox1, bbox2):
                        new_result['paragraph'].append(merge_boxes(bbox1, bbox2))
                        used_indices.add(i)
                        used_indices.add(j)
                        was_merged = True
                        break
                        
                if not was_merged and i not in used_indices:
                    new_result['paragraph'].append(bbox1)
                    
            # добавляем оставшиеся неиспользованные элементы
            for i in range(result_paragraph_len):
                if i not in used_indices:
                    new_result['paragraph'].append(result['paragraph'][i])
                    
            result = new_result.copy()
        new_result = result.copy()
        result['paragraph'] = []
        for bbox in new_result['paragraph']:
            if not (bbox in result['paragraph']):
                result['paragraph'].append(bbox)
        
        new_result = result.copy()
        new_result['paragraph'] = []
        for i in range(len(result['paragraph'])):
            bbox1 = result['paragraph'][i]
            to_check = result['paragraph'][:i] + result['paragraph'][i+1:]
            if not any(is_inside(bbox1, bbox2) for bbox2 in to_check):
                new_result['paragraph'].append(bbox1)
        result = new_result.copy()

    return result

def extract_elements(page, image_filename):
    """Извлекает элементы страницы и определяет их типы."""
    
    page_dict = page.get_text("dict")
    page_width = page.rect.width
    page_height = page.rect.height

    header_threshold = 0.085 * page_height  
    footer_threshold = 0.085 * page_height
    
    elements = {
        "table": [],
        "title": [],
        "paragraph": [],
        "formula": [],
        "header": [],
        "footer": [],
        "footnote": [],
        "numbered_list": [],
        "marked_list": [],
        "table_signature": [],
        "picture_signature": [],
        "picture": [],
        "image_width": float(page_width),
        "image_height": float(page_height),
        "image_path": os.path.join(IMAGE_DIR, image_filename)
    }

    # 1. Находим все рисунки (используем оба метода)
    restricted_areas = []
    
    # метод 1: через get_images
    for img in page.get_images():
        try:
            xref = img[0]  # получаем xref изображения
            rect = page.get_image_rects(xref)  # получаем все вхождения изображения
            if rect:
                for r in rect:
                    bbox = [float(r.x0), float(r.y0), float(r.x1), float(r.y1)]
                    elements["picture"].append(bbox)
                    restricted_areas.append(bbox)
        except:
            continue

    # метод 2: через get_drawings
    for drawing in page.get_drawings():
        if drawing["type"] == "image":
            bbox = [float(x) for x in drawing["rect"]]
            if not any(check_overlap(bbox, existing) for existing in elements["picture"]):
                elements["picture"].append(bbox)
                restricted_areas.append(bbox)

    # 2. Находим таблицы
    tables = page.find_tables()
    for table in tables:
        bbox = [float(x) for x in table.bbox]
        elements["table"].append(bbox)
        restricted_areas.append(bbox)

    # 3. Собираем текстовые блоки
    text_blocks = []
    for block in page_dict["blocks"]:
        if block.get("type") != 0:
            continue
            
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue

                bbox = [float(x) for x in span["bbox"]]

                # пропускаем блоки в запрещенных областях
                if any(check_overlap(bbox, area) for area in restricted_areas):
                    continue

                font = span.get("font", "").lower()
                color = span.get("color", "")
                is_not_black = bool(color and color not in ["", "black", "#000000", "(0, 0, 0)", "000000"])
                is_bold = ('bold' in span['font'].lower())

                block_info = {
                    "bbox": bbox,
                    "text": text,
                    "font": font,
                    "is_not_black": is_not_black,
                    "y_coord": bbox[1],
                    "is_bold": is_bold
                }
                text_blocks.append(block_info)

    # сортируем блоки по вертикали
    text_blocks.sort(key=lambda x: x["y_coord"])

    was_annons_of_endnotes = False

    # 5. Классифицируем текстовые блоки
    for block in text_blocks:
        text = block["text"]
        bbox = list(block["bbox"])
        font = block["font"]
        y_coord = bbox[1]
        
        block_type = None

        # 0. проверяем header и footer
        if y_coord >= (page_height - footer_threshold):
            elements["footer"].append(bbox)
        elif y_coord <= header_threshold:
            elements["header"].append(bbox)

        # 1. проверяем, было ли объявление концевых сносок
        elif was_annons_of_endnotes:
            block_type = 'numbered_list'

        # 2. проверяем формулы
        elif block['font'] == 'cambria math':
            block_type = "formula"
            
        # 3. проверяем списки
        elif text == '\uf0b7':
            block_type = "marked_list"
        elif re.match(r'^\d+\.', text.strip()):
            block_type = "numbered_list"

        # 4. проверяем подписи таблиц
        elif re.match(r'^(Табл\.\s+\d+\.\s|Таблица\s+\d+\s-\s|Таблица\.)', text):
            block_type = "table_signature"
        
        # 5. проверяем заголовки
        elif block["is_bold"]:
            block_type = "title"
                
        # 6. проверяем подписи рисунков
        elif re.match(r'^(Рис\.|Рисунок)\s+\d+', text):
            block_type = "picture_signature"
        else:
            block_type = "paragraph"

        # добавляем bbox в соответствующий список
        if block_type:
            elements[block_type].append(bbox)

        if text == 'Концевые сноски':
            was_annons_of_endnotes = True

    new_elements = elements.copy()
    new_elements['paragraph'] = []

    for bbox in elements['paragraph']:
        is_added = False
        # проверяем, есть ли левее этого блока блок списка
        for nl_box in elements['numbered_list']:
            vertical_overlap = not (bbox[3] < nl_box[1] or bbox[1] > nl_box[3])
            is_lefter = (bbox[0] > nl_box[2])
            if vertical_overlap and is_lefter:
                new_elements['numbered_list'].append(bbox)
                is_added = True
                break

        if is_added:
            continue

        for ml_box in elements['marked_list']:
            vertical_overlap = not (bbox[3] < ml_box[1] or bbox[1] > ml_box[3])
            is_lefter = (bbox[0] > ml_box[2])
            if vertical_overlap and is_lefter:
                new_elements['marked_list'].append(bbox)
                is_added = True
                break

        if is_added:
            continue

        new_elements["paragraph"].append(bbox) 
        
    elements = new_elements.copy()
    del new_elements

    elements = merge_blocks(elements)

    # теперь найдем (и добавим, если нашли) сноски
    for block in text_blocks:
        if block['text'][0] + block['text'][-1] == '[]':
            bbox = list(block["bbox"])
            elements['footnote'].append(bbox)
    
    return elements

def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        image_filename = f"{pdf_name}_{page_num + 1}.png"   
        image_path = os.path.join(IMAGE_DIR, image_filename)
        if not os.path.exists(image_path):
            print(f"Изображение не найдено: {image_path}, пропуск страницы.")
            continue

        elements = extract_elements(page, image_filename)

        # сохранение JSON
        json_filename = f"{pdf_name}_{page_num + 1}.json"
        json_path = os.path.join(JSON_DIR, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(elements, f, ensure_ascii=False, indent=4)

        # визуализация
        if VISUALISE:
            zoom = 300 / 72  
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # создаем временный путь для базового изображения
            temp_image_path = os.path.join(IMAGE_DIR, f"{pdf_name}_{page_num + 1}_temp.png")
            pix.save(temp_image_path)

            visualization_filename = f"{pdf_name}_{page_num + 1}_vis.png"
            visualization_path = os.path.join(VISUAL_DIR, visualization_filename)
            visualize_elements(temp_image_path, elements, visualization_path, pix.width, pix.height)
            
            # удаляем временный файл
            os.remove(temp_image_path)

    doc.close()

def main():
    print("Обработка начата...")
    cnt = 1
    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(PDF_DIR, filename)
            process_pdf(pdf_path)
            print(f"Успешно обработано {cnt} файлов")
            cnt += 1

if __name__ == "__main__":
    main()