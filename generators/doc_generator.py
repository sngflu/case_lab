import os
import random
import uuid
import tempfile
from docx import Document
from docx.shared import Cm, Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START, WD_ORIENT, WD_SECTION
from docx.oxml import OxmlElement, ns
from docx.oxml.ns import qn
from docx.oxml.ns import nsdecls
from faker import Faker
import math2docx
import matplotlib.pyplot as plt

# настройка Faker для генерации фиктивного текста на русском языке
fake = Faker('ru_RU')

# константы для цвета фона таблиц
colors_list = ['FF0000', '00FF00', '0000FF', 'FFFF00', 'FF00FF', '00FFFF', 'FFFFFF', '000000']

class DocumentState:
    """Класс для отслеживания состояния документа, включая текущие колонки, ориентацию и т.д."""
    def __init__(self, document):
        self.current_columns = 1  # текущие колонки (1, 2 или 3)
        self.document = document
        self.multicol_sections_added = {'2': False, '3': False}
        self.elements_in_multicol = 0  # счётчик элементов в многоколонной секции
        self.max_elements_multicol = 10  # максимальное количество элементов в секции
        self.in_multicol = False  # флаг, находится ли документ сейчас в многоколонной секции
        self.current_orientation = WD_ORIENT.PORTRAIT  # текущая ориентация
        self.multicol_table = None  # Таблица, используемая для многоколонной секции
        self.current_multicol_cell = None  # Текущая ячейка таблицы для вставки контента
        self.multicol_col_index = 0  # Индекс текущей колонки
    
    def can_add_multicolumn(self, num_cols):
        """Проверяет, можно ли добавить секцию с num_cols колонками."""
        return not self.multicol_sections_added.get(str(num_cols), False)

    def start_multicolumn(self, num_cols):
        """Запускает многоколонную секцию с использованием полностью прозрачной таблицы."""
        if not self.can_add_multicolumn(num_cols):
            return False

        # создаём таблицу с нужным количеством колонок
        table = self.document.add_table(rows=1, cols=num_cols)
        table.autofit = False  # Отключаем автонастройку размера

        # настраиваем ячейки таблицы для полной прозрачности
        for row in table.rows:
            for cell in row.cells:
                # устанавливаем прозрачность границ ячейки
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                tcBorders = OxmlElement('w:tcBorders')
                for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                    border = OxmlElement(f'w:{border_name}')
                    border.set(qn('w:val'), 'nil')  
                    tcBorders.append(border)
                tcPr.append(tcBorders)

                # убираем заливку (фон) ячейки, если она есть
                cell_shading = OxmlElement('w:shd')
                cell_shading.set(qn('w:val'), 'clear')  
                tcPr.append(cell_shading)

        self.multicol_table = table
        self.current_multicol_cell = table.rows[0].cells[0]
        self.multicol_col_index = 0

        self.current_columns = num_cols
        self.in_multicol = True
        self.elements_in_multicol = 0
        self.multicol_sections_added[str(num_cols)] = True
        return True

    def end_multicolumn(self):
        """Заканчивает текущую многоколонную секцию."""
        if not self.in_multicol:
            return

        # добавляем перенос строки после таблицы для разделения
        self.document.add_paragraph()

        # сбрасываем состояния
        self.multicol_table = None
        self.current_multicol_cell = None
        self.multicol_col_index = 0
        self.current_columns = 1
        self.in_multicol = False

    def get_current_multicol_cell(self):
        """Возвращает текущую ячейку таблицы для вставки контента и обновляет индекс колонки при необходимости."""
        if not self.in_multicol or not self.multicol_table:
            return None

        cell = self.multicol_table.rows[0].cells[self.multicol_col_index]
        # обновляем индекс колонки для следующего элемента
        self.multicol_col_index = (self.multicol_col_index + 1) % self.current_columns
        return cell

    def can_start_multicolumn(self):
        """Проверяет, можно ли начать новую многоколонную секцию."""
        return (self.can_add_multicolumn(2) or self.can_add_multicolumn(3))

def add_table_caption(document, before=True):
    """Добавляет подпись к таблице перед или после таблицы."""
    caption_type = random.choice(['Табл. {num}. {text}', 'Таблица {num} - {text}', 'Таблица. {text}'])
    table_num = random.randint(1, 100)
    if 'num' in caption_type:
        if caption_type.startswith('Таблица.'):
            caption_text = caption_type.format(text=fake.sentence(nb_words=4))
        else:
            caption_text = caption_type.format(num=table_num, text=fake.sentence(nb_words=4))
    else:
        caption_text = f"Таблица. {fake.sentence(nb_words=4)}"

    p = document.add_paragraph(caption_text, style='Caption')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.runs[0].font.size = Pt(random.randint(10, 12))
    p.runs[0].font.italic = True

def add_table(document, doc_state):
    """Добавляет таблицу с подписью в документ, случайно располагая подпись перед или после таблицы."""
    if doc_state.in_multicol:
        # в многоколонной секции таблицы добавлять нельзя
        return

    # решаем, где разместить подпись: перед или после
    caption_before = random.choice([True, False])

    # добавление подписи
    if caption_before:
        add_table_caption(document, before=True)

    # добавление самой таблицы
    table_styles = get_table_styles(document)
    num_rows = random.randint(5, 10)
    num_cols = random.randint(3, 6)

    # создаём таблицу
    table = document.add_table(rows=num_rows, cols=num_cols)
    table.style = random.choice(table_styles) if table_styles else 'Table Grid'
    table.alignment = random.choice([
        WD_TABLE_ALIGNMENT.LEFT,
        WD_TABLE_ALIGNMENT.CENTER,
        WD_TABLE_ALIGNMENT.RIGHT
    ])
    table.autofit = False

    # установка ширины таблицы
    table_width = Cm(18)  

    # генерация цветов для альтернативного стиля
    alternating_style = False
    color_a, color_b = None, None

    for row_idx, row in enumerate(table.rows):
        row.height = Pt(12)
        for idx, cell in enumerate(row.cells):
            cell.width = table_width / num_cols
            cell.text = ""  

            # выбор стиля таблицы
            table_style_option = random.choice(['random', 'single_color', 'alternating_color'])
            if table_style_option == 'alternating_color':
                if not alternating_style:
                    # инициализируем цвета для чередования
                    color_a, color_b = random.sample(colors_list, 2)
                    alternating_style = True
                # устанавливаем цвет фона в зависимости от чётности строки
                row_color = color_a if row_idx % 2 == 0 else color_b
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:val'), 'clear')
                shading_elm.set(qn('w:color'), 'auto')
                shading_elm.set(qn('w:fill'), row_color)
                cell._tc.get_or_add_tcPr().append(shading_elm)
                # добавляем случайный текст
                cell.text = fake.text(max_nb_chars=random.randint(5, 50)) if random.choice([True, False]) else str(fake.random_number(digits=5))
            else:
                if table_style_option == 'random':
                    if random.choice([True, False]):
                        fill_color = random.choice(colors_list)
                        shading_elm = OxmlElement('w:shd')
                        shading_elm.set(qn('w:val'), 'clear')
                        shading_elm.set(qn('w:color'), 'auto')
                        shading_elm.set(qn('w:fill'), fill_color)
                        cell._tc.get_or_add_tcPr().append(shading_elm)
                elif table_style_option == 'single_color':
                    single_color = random.choice(colors_list)
                    shading_elm = OxmlElement('w:shd')
                    shading_elm.set(qn('w:val'), 'clear')
                    shading_elm.set(qn('w:color'), 'auto')
                    shading_elm.set(qn('w:fill'), single_color)
                    cell._tc.get_or_add_tcPr().append(shading_elm)

                # добавляем случайный текст
                cell.text = fake.text(max_nb_chars=random.randint(5, 50)) if random.choice([True, False]) else str(fake.random_number(digits=5))

                # настройка выравнивания текста в ячейках
                cell_paragraph = cell.paragraphs[0]
                cell_paragraph.alignment = random.choice([
                    WD_ALIGN_PARAGRAPH.LEFT,
                    WD_ALIGN_PARAGRAPH.CENTER,
                    WD_ALIGN_PARAGRAPH.RIGHT,
                    WD_ALIGN_PARAGRAPH.JUSTIFY
                ])

                # настройка шрифта
                if cell_paragraph.runs:
                    run = cell_paragraph.runs[0]
                    run.font.size = Pt(random.randint(8, 12))

    if not caption_before:
        add_table_caption(document, before=False)

    # увеличиваем счётчик элементов в многоколонной секции
    if doc_state.in_multicol:
        doc_state.elements_in_multicol += 1
        if doc_state.elements_in_multicol >= doc_state.max_elements_multicol:
            doc_state.end_multicolumn()

def add_footnote(paragraph, text, footnote_number):
    """Добавляет сноску в абзац."""
    run = paragraph.add_run(f"[{footnote_number}]")
    run.font.superscript = True
    run.font.size = Pt(8)
    paragraph.add_run(f" {text}")

def add_document_end_footnotes(document, end_footnotes):
    """Добавляет список концевых сносок в конце документа."""
    if not end_footnotes:
        return
    # добавляем раздел перед концевыми сносками для одноколоночного режима
    document.add_section(WD_SECTION_START.NEW_PAGE)
    p = document.add_paragraph("Концевые сноски", style='Heading 2')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].font.size = Pt(random.randint(14, 18))
    p.runs[0].font.bold = True
    for idx, footnote in enumerate(end_footnotes, 1):
        p = document.add_paragraph(f"{idx}. {footnote}", style='Normal')
        p.runs[0].font.size = Pt(random.randint(10, 14))
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

def add_image(document, doc_state):
    """Добавляет изображение с подписью в документ, с возможностью изменения размера изображения и различными стилями подписи."""
    pic_path = generate_random_plot_image(doc_state)
    if not os.path.exists(pic_path):
        return

    img_width = min(Inches(random.uniform(4, 6)), Inches(6))  # максимальная ширина 6 дюймов

    # случайное определение текста подписи
    caption_variants = [
        f"Рис. {random.randint(1, 100)}",
        f"Рисунок {random.randint(1, 100)} -",
        f"Рисунок {random.randint(1, 100)}"
    ]
    caption_text = random.choice(caption_variants) + f" {fake.sentence(nb_words=5)}"

    # случайное определение уменьшения размера шрифта подписи
    caption_font_size = Pt(random.randint(8, 10))

    # случайное выравнивание подписи (чаще по центру)
    caption_alignment = random.choices(
        [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT],
        weights=[0.6, 0.2, 0.2]
    )[0]

    # функция добавления изображения с уменьшением размера при необходимости
    def add_resizable_image(container, width):
        run = container.add_run()
        try:
            run.add_picture(pic_path, width=width)
            return True
        except Exception as e:
            return False

    # чаще добавляем подпись после изображения
    caption_before = random.choices([True, False], weights=[0.4, 0.6])[0]

    # создание контейнера для изображения и подписи
    if doc_state.in_multicol:
        current_cell = doc_state.get_current_multicol_cell()
        if current_cell is None:
            return
        p_container = current_cell.add_paragraph()
        p_container.paragraph_format.keep_with_next = True
    else:
        p_container = document.add_paragraph()
        p_container.paragraph_format.keep_with_next = True

    # добавление подписи перед изображением, если выбрана эта опция
    if caption_before:
        p_caption = p_container.add_run(caption_text)
        p_caption.font.size = caption_font_size
        p_container.paragraph_format.keep_with_next = True
        p_container.alignment = caption_alignment
        p_container.add_run("\n")  # Добавляем перенос строки

    # добавление изображения и уменьшение его размера при необходимости
    while not add_resizable_image(p_container, img_width) and img_width > Cm(1):
        img_width -= Cm(0.5)

    # добавление подписи после изображения, если не выбрана опция "перед"
    if not caption_before:
        p_caption = p_container.add_run(f"\n{caption_text}")
        p_caption.font.size = caption_font_size
        p_container.paragraph_format.keep_with_next = True
        p_container.alignment = caption_alignment

    # удаление временного файла изображения
    os.remove(pic_path)

    # увеличение счётчика элементов в многоколонной секции
    if doc_state.in_multicol:
        doc_state.elements_in_multicol += 1
        if doc_state.elements_in_multicol >= doc_state.max_elements_multicol:
            doc_state.end_multicolumn()

def make_paragraph_keep_together(paragraph):
    """Применяет свойства для предотвращения разрыва страницы внутри абзаца."""
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    keep_together = OxmlElement('w:keepTogether')
    keep_together.set(qn('w:val'), '1')
    pPr.append(keep_together)

    keep_with_next = OxmlElement('w:keepNext')
    keep_with_next.set(qn('w:val'), '1')
    pPr.append(keep_with_next)

def make_run_keep_with_next(run):
    """Применяет свойства к запуску для предотвращения разрыва страницы между элементами."""
    r = run._r
    rPr = r.get_or_add_rPr()
    keep_with_next = OxmlElement('w:keepNext')
    keep_with_next.set(qn('w:val'), '1')
    rPr.append(keep_with_next)

def add_heading(document, level=2):
    """Добавляет заголовок заданного уровня в документ."""
    heading_text = fake.sentence(nb_words=6)
    p = document.add_heading(level=level)  
    run = p.add_run(heading_text) 
    run.font.size = Pt(random.randint(14 + (level - 1) * 2, 20 + (level - 1) * 2))
    if random.choice([True, False]):
        run.bold = True
    if random.choice([True, False]):
        run.italic = True
    heading_alignment = random.choice([
        WD_ALIGN_PARAGRAPH.LEFT,
        WD_ALIGN_PARAGRAPH.CENTER,
        WD_ALIGN_PARAGRAPH.RIGHT
    ])
    p.paragraph_format.space_before = Pt(12)
    p.alignment = heading_alignment

def add_heading_to_cell(cell, level=2):
    """Добавляет заголовок заданного уровня в указанную ячейку таблицы."""
    p = cell.add_paragraph(style=f'Heading {level}')
    p.text = fake.sentence(nb_words=6)
    p.alignment = random.choice([
        WD_ALIGN_PARAGRAPH.LEFT,
        WD_ALIGN_PARAGRAPH.CENTER,
        WD_ALIGN_PARAGRAPH.RIGHT
    ])

def add_text(document, doc_state, text, font_size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT):
    """Добавляет абзац текста в документ с заданным форматированием."""
    p = document.add_paragraph(text)
    run = p.runs[0]
    run.font.size = Pt(font_size)
    p.alignment = alignment

    # 50% шанс добавить красную строку
    if random.choice([True, False]):
        p.paragraph_format.first_line_indent = Cm(1.25)  
    else:
        p.paragraph_format.first_line_indent = Cm(0) 

    # разнообразие межстрочного интервала
    p.paragraph_format.space_after = Pt(random.randint(6, 12))

    # предотвращаем разрыв страницы внутри абзаца
    make_paragraph_keep_together(p)

def add_text_to_cell(cell, text, font_size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT):
    """Добавляет абзац текста в указанную ячейку таблицы с заданным форматированием."""
    p = cell.add_paragraph(text)
    run = p.runs[0]
    run.font.size = Pt(font_size)
    p.alignment = alignment

    # 50% шанс добавить красную строку
    if random.choice([True, False]):
        p.paragraph_format.first_line_indent = Cm(1.25) 
    else:
        p.paragraph_format.first_line_indent = Cm(0)  

    # разнообразие межстрочного интервала
    p.paragraph_format.space_after = Pt(random.randint(6, 12))

    # предотвращаем разрыв страницы внутри абзаца
    make_paragraph_keep_together(p)

def add_footnote_to_cell(cell, text, footnote_number):
    """Добавляет сноску к элементу в ячейке таблицы."""
    p = cell.add_paragraph()
    run = p.add_run(f"[{footnote_number}]")
    run.font.superscript = True
    run.font.size = Pt(8)
    p.add_run(f" {text}")

def add_bulleted_list_to_cell(cell, num_items=5):
    """Добавляет маркированный список в указанную ячейку таблицы."""
    for _ in range(num_items):
        p = cell.add_paragraph(fake.sentence(nb_words=6), style='List Bullet')
        p.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        p.runs[0].font.size = Pt(random.randint(10, 14))
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.space_after = Pt(6)

def add_formula_to_cell(cell, generated_formulas):
    """Добавляет формулу в указанную ячейку таблицы."""
    formula = generate_complex_formula(generated_formulas)
    if not formula:
        return
    try:
        math2docx.add_math(cell.add_paragraph(), formula)
    except Exception:
        pass  # ничего не добавляем

def add_numbered_list(document, num_items=5):
    """Добавляет нумерованный список в документ."""
    for _ in range(num_items):
        p = document.add_paragraph(fake.sentence(nb_words=6), style='List Number')
        p.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        p.runs[0].font.size = Pt(random.randint(10, 14))
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.space_after = Pt(6)

def add_numbered_list_to_cell(cell, num_items=5):
    """Добавляет нумерованный список в указанную ячейку таблицы."""
    for _ in range(num_items):
        p = cell.add_paragraph(fake.sentence(nb_words=6), style='List Number')
        p.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        p.runs[0].font.size = Pt(random.randint(10, 14))
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.space_after = Pt(6)


def add_bulleted_list(document, num_items=5):
    """Добавляет маркированный список в документ."""
    for _ in range(num_items):
        p = document.add_paragraph(fake.sentence(nb_words=6), style='List Bullet')
        p.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        p.runs[0].font.size = Pt(random.randint(10, 14))
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.space_after = Pt(6)

def add_formula(document, generated_formulas):
    """Добавляет сгенерированную формулу как Office Math объект в документ."""
    formula = generate_complex_formula(generated_formulas)
    if not formula:
        return
    latex_formula = formula
    paragraph = document.add_paragraph()
    try:
        math2docx.add_math(paragraph, latex_formula)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    except Exception as e:
        pass

    # предотвращаем разрыв страницы между формулой и следующим элементом
    paragraph.paragraph_format.keep_with_next = True

def generate_complex_formula(generated_formulas):
    """Генерирует уникальную сложную LaTeX формулу."""
    formula_types = ['integral', 'sum', 'polynomial', 'fraction', 'product']
    formula_type = random.choice(formula_types)
    
    if formula_type == 'integral':
        a = random.randint(1, 10)
        b = random.randint(1, 20)
        c = random.randint(1, 10)
        formula = f"\\int_{{0}}^{{{b}}} {a}x^{{{c}}} \\, dx"
        
    elif formula_type == 'sum':
        n = random.randint(1, 20)
        power = random.randint(1, 5)
        formula = f"\\sum_{{i=1}}^{{{n}}} i^{{{power}}}"
        
    elif formula_type == 'polynomial':
        degree = random.randint(2, 5)
        coefficients = [random.randint(1, 10) for _ in range(degree + 1)]
        terms = []
        for i, coeff in enumerate(coefficients):
            power = degree - i
            if power > 1:
                terms.append(f"{coeff}x^{{{power}}}")
            elif power == 1:
                terms.append(f"{coeff}x")
            else:
                terms.append(f"{coeff}")
        formula = " + ".join(terms)
        
    elif formula_type == 'fraction':
        # генерация двух полиномов для числителя и знаменателя
        degree_num = random.randint(1, 3)
        degree_den = random.randint(1, 3)
        coefficients_num = [random.randint(1, 10) for _ in range(degree_num + 1)]
        coefficients_den = [random.randint(1, 10) for _ in range(degree_den + 1)]
        
        # создание числителя
        terms_num = []
        for i, coeff in enumerate(coefficients_num):
            power = degree_num - i
            if power > 1:
                terms_num.append(f"{coeff}x^{{{power}}}")
            elif power == 1:
                terms_num.append(f"{coeff}x")
            else:
                terms_num.append(f"{coeff}")
        numerator = " + ".join(terms_num)
        
        # создание знаменателя
        terms_den = []
        for i, coeff in enumerate(coefficients_den):
            power = degree_den - i
            if power > 1:
                terms_den.append(f"{coeff}x^{{{power}}}")
            elif power == 1:
                terms_den.append(f"{coeff}x")
            else:
                terms_den.append(f"{coeff}")
        denominator = " + ".join(terms_den)
        
        formula = f"\\frac{{{numerator}}}{{{denominator}}}"
        
    elif formula_type == 'product':
        # произведение двух полиномов
        degree_p1 = random.randint(1, 3)
        degree_p2 = random.randint(1, 3)
        coeff_p1 = random.randint(1, 10)
        coeff_p2 = random.randint(1, 10)
        
        # полином 1
        poly1_terms = []
        for i in range(degree_p1 +1):
            power = degree_p1 - i
            if power > 1:
                poly1_terms.append(f"{coeff_p1}x^{{{power}}}")
            elif power ==1:
                poly1_terms.append(f"{coeff_p1}x")
            else:
                poly1_terms.append(f"{coeff_p1}")
        poly1 = " + ".join(poly1_terms)
        
        # полином 2
        poly2_terms = []
        for i in range(degree_p2 +1):
            power = degree_p2 - i
            if power >1:
                poly2_terms.append(f"{coeff_p2}x^{{{power}}}")
            elif power ==1:
                poly2_terms.append(f"{coeff_p2}x")
            else:
                poly2_terms.append(f"{coeff_p2}")
        poly2 = " + ".join(poly2_terms)
        
        formula = f"({poly1}) \\cdot ({poly2})"
    else:
        return None

    # проверяем уникальность
    if formula in generated_formulas:
        return generate_complex_formula(generated_formulas)
    generated_formulas.add(formula)
    return formula

def generate_random_plot_image(doc_state):
    """Генерирует случайный график и сохраняет его во временный файл."""
    plot_type = random.choice(['line', 'bar', 'scatter', 'box', 'pie', 'hist'])
    fig, ax = plt.subplots(figsize=(4, 3))
    if plot_type == 'line':
        x = range(10)
        y = [random.randint(0, 100) for _ in x]
        ax.plot(x, y, marker='o')
        ax.set_title('Линейный график')
    elif plot_type == 'bar':
        categories = [fake.word() for _ in range(random.randint(3, 7))]
        values = [random.randint(10, 100) for _ in categories]
        ax.bar(categories, values, color=random.choice(['blue', 'green', 'red', 'cyan', 'magenta']))
        ax.set_title('Столбчатая диаграмма')
    elif plot_type == 'scatter':
        x = [random.uniform(0, 10) for _ in range(15)]
        y = [random.uniform(0, 10) for _ in range(15)]
        ax.scatter(x, y, color=random.choice(['blue', 'green', 'red', 'cyan', 'magenta']))
        ax.set_title('Точечная диаграмма')
    elif plot_type == 'box':
        data = [sorted([random.randint(0, 100) for _ in range(random.randint(10, 20))]) for _ in range(random.randint(2, 5))]
        ax.boxplot(data)
        ax.set_title('Боксплот')
    elif plot_type == 'pie':
        sizes = [random.randint(10, 100) for _ in range(random.randint(3, 6))]
        labels = [fake.word() for _ in sizes]
        ax.pie(sizes, labels=labels, autopct='%1.1f%%')
        ax.set_title('Круговая диаграмма')
    elif plot_type == 'hist':
        data = [random.gauss(50, 15) for _ in range(100)]
        ax.hist(data, bins=10, color=random.choice(['blue', 'green', 'red', 'cyan', 'magenta']))
        ax.set_title('Гистограмма')
    ax.axis('off')  # скрываем оси для чистоты изображения
    plt.tight_layout()

    # сохранение изображения с учётом режима колонок
    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4()
    image_path = os.path.join(temp_dir, f"plot_{unique_id}.png")
    plt.savefig(image_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    return image_path

def add_header_footer(document, header_text=None, footer_text=None):
    """Добавляет текст в колонтитулы документа."""
    section = document.sections[0]
    header = section.header
    footer = section.footer

    if header_text:
        header_para = header.paragraphs[0]
        header_para.text = header_text
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_para.runs[0].font.size = Pt(12)

    if footer_text:
        footer_para = footer.paragraphs[0]
        footer_para.text = footer_text
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_para.runs[0].font.size = Pt(12)

def get_table_styles(document):
    """Получает все стили таблиц в документе."""
    styles = document.styles
    table_styles = []
    temp_table = document.add_table(rows=1, cols=1)
    for s in styles:
        if 'Table' in s.name or 'Таблица' in s.name:
            try:
                temp_table.style = s
                table_styles.append(s.name)
            except:
                pass
    # удаляем временную таблицу
    temp_table._element.getparent().remove(temp_table._element)
    return table_styles

def set_section_orientation(section, orientation=WD_ORIENT.PORTRAIT):
    """Устанавливает ориентацию секции документа."""
    new_width, new_height = (section.page_height, section.page_width) if orientation == WD_ORIENT.LANDSCAPE else (section.page_width, section.page_height)
    section.orientation = orientation
    section.page_width = new_width
    section.page_height = new_height

def add_random_elements(document, doc_state, end_footnotes, generated_formulas, last_element=None):
    """Добавляет случайные элементы в документ в зависимости от текущего состояния колонки."""
    # определяем возможные элементы
    elements = ['heading', 'text', 'list', 'formula', 'footnote']
    if not doc_state.in_multicol:
        elements.extend(['image', 'table'])

    # настройки вероятностей появления элементов
    element_weights = {
        'heading': 15,
        'text': 40,
        'list': 10,
        'formula': 15,
        'image': 5,
        'table': 5,
        'footnote': 15
    }

    # исключаем элемент, если последний был таким же, чтобы избежать повторений
    if last_element:
        elements = [elem for elem in elements if elem != last_element]
        weights = [element_weights[elem] for elem in elements]
    else:
        weights = [element_weights[elem] for elem in elements]

    element_type = random.choices(elements, weights=weights, k=1)[0]

    # добавляем выбранный элемент
    if element_type == 'heading':
        level = random.choice([2, 3])
        if doc_state.in_multicol:
            current_cell = doc_state.get_current_multicol_cell()
            if current_cell:
                add_heading_to_cell(current_cell, level=level)
        else:
            add_heading(document, level=level)
    elif element_type == 'text':
        text = fake.paragraph(nb_sentences=random.randint(3, 8))
        font_size = random.randint(10, 14)
        alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.RIGHT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        if doc_state.in_multicol:
            current_cell = doc_state.get_current_multicol_cell()
            if current_cell:
                add_text_to_cell(current_cell, text, font_size, alignment)
        else:
            add_text(document, doc_state, text, font_size, alignment)
    elif element_type == 'list':
        list_type = random.choice(['numbered', 'bulleted'])
        num_items = random.randint(3, 6)
        if doc_state.in_multicol:
            current_cell = doc_state.get_current_multicol_cell()
            if current_cell:
                if list_type == 'numbered':
                    add_numbered_list_to_cell(current_cell, num_items)
                else:
                    add_bulleted_list_to_cell(current_cell, num_items)
        else:
            if list_type == 'numbered':
                add_numbered_list(document, num_items)
            else:
                add_bulleted_list(document, num_items)
    elif element_type == 'formula':
        if doc_state.in_multicol:
            current_cell = doc_state.get_current_multicol_cell()
            if current_cell:
                add_formula_to_cell(current_cell, generated_formulas)
        else:
            add_formula(document, generated_formulas)
    elif element_type == 'footnote':
        footnote_text = fake.sentence(nb_words=10)
        if doc_state.in_multicol:
            current_cell = doc_state.get_current_multicol_cell()
            if current_cell:
                add_footnote_to_cell(current_cell, footnote_text, len(end_footnotes) + 1)
        else:
            p = document.add_paragraph()
            add_footnote(p, footnote_text, len(end_footnotes) + 1)
        end_footnotes.append(footnote_text)
    elif element_type == 'image' and not doc_state.in_multicol:
        add_image(document, doc_state)
    elif element_type == 'table' and not doc_state.in_multicol:
        add_table(document, doc_state)
    

    return element_type  # возвращаем тип последнего добавленного элемента
    
def generate_document(doc_id, output_dir, num_iterations=100):
    """Генерирует один документ с заданным количеством итераций добавления элементов."""
    document = Document()
    doc_state = DocumentState(document)

    # устанавливаем ориентацию первой секции
    set_section_orientation(document.sections[-1], WD_ORIENT.PORTRAIT)

    # добавление колонтитулов
    header_text = fake.sentence(nb_words=4)
    footer_text = fake.sentence(nb_words=4)
    add_header_footer(document, header_text=header_text, footer_text=footer_text)

    generated_formulas = set()
    end_footnotes = [] 
    last_element = None 

    # начальная контент (одноколоночный)
    for _ in range(10):
        last_element = add_random_elements(document, doc_state, end_footnotes, generated_formulas, last_element)

    # основной цикл генерации контента
    for _ in range(num_iterations - 10):
        # решаем, вставлять ли новую секцию с возможным изменением ориентации
        if random.random() < 0.2:  # 20% шанс изменить ориентацию
            # выбираем ориентацию: 25% альбомная, 75% книжная
            orientation = WD_ORIENT.LANDSCAPE if random.random() < 0.25 else WD_ORIENT.PORTRAIT
            # добавляем новую секцию
            section = document.add_section(WD_SECTION_START.CONTINUOUS)
            set_section_orientation(section, orientation)
            doc_state.current_orientation = orientation

        # решаем, вставлять ли многоколонную секцию
        if doc_state.can_start_multicolumn() and not doc_state.in_multicol:
            if random.random() < 0.1:  # 10% шанс начать многоколонную секцию
                # выбираем тип колонок
                possible_cols = []
                if doc_state.can_add_multicolumn(2):
                    possible_cols.append(2)
                if doc_state.can_add_multicolumn(3):
                    possible_cols.append(3)
                if possible_cols:
                    num_cols = random.choice(possible_cols)
                    started = doc_state.start_multicolumn(num_cols)
                    if started:
                        # добавляем контент в многоколонную секцию
                        for _ in range(random.randint(5, 10)):
                            last_element = add_random_elements(document, doc_state, end_footnotes, generated_formulas, last_element)
                        # прерываем многоколонную секцию
                        doc_state.end_multicolumn()
                        continue

        # добавляем обычные элементы
        last_element = add_random_elements(document, doc_state, end_footnotes, generated_formulas, last_element)

    # проверка, чтобы документ не заканчивался многоколонной секцией
    if doc_state.in_multicol:
        doc_state.end_multicolumn()

    # добавляем концевые сноски
    add_document_end_footnotes(document, end_footnotes)

    # сохранение документа
    output_path = os.path.join(output_dir, f'demo_{doc_id}.docx')
    try:
        document.save(output_path)
    except Exception as e:
        print(f"Ошибка при сохранении документа: {e}")


def main():
    output_dir = './data/docx'
    os.makedirs(output_dir, exist_ok=True)
    num_docs = 3  # размер выборки, потом увеличим до 10000
    for doc_id in range(num_docs):
        # гарантируем, что многоколонные секции не будут на первой и последней страницах
        generate_document(doc_id, output_dir)
        if (doc_id + 1) % 100 == 0:
            print(f'Создано {doc_id + 1} документов')

if __name__ == "__main__":
    main()