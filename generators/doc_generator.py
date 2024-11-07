import os
import random
import uuid
import tempfile
from docx import Document
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, Inches
import math2docx
from faker import Faker
import matplotlib.pyplot as plt

# настройка Faker для генерации фиктивного текста на русском языке
fake = Faker('ru_RU')

# константы для цвета фона таблиц
colors_list = ['FF0000', '00FF00', '0000FF', 'FFFF00',
               'FF00FF', '00FFFF', 'FFFFFF', '000000']

class DocumentState:
    """ Класс для отслеживания состояния документа, включая текущие колонки, ориентацию и т.д. """
    def __init__(self, document):
        self.current_columns = 1  # текущие колонки (1, 2 или 3)
        self.document = document
        self.multicol_sections_added = {'2': False, '3': False}
        self.elements_in_multicol = 0  # счётчик элементов в многоколонной секции
        self.max_elements_multicol = 10  # максимальное количество элементов в секции
        self.in_multicol = False  # флаг, находится ли документ сейчас в многоколонной секции
        self.current_orientation = WD_ORIENT.PORTRAIT  # текущая ориентация

    def can_add_multicolumn(self, num_cols):
        """Проверяет, можно ли добавить секцию с num_cols колонками."""
        return not self.multicol_sections_added.get(str(num_cols), False)

    def start_multicolumn(self, num_cols):
        """Запускает многоколонную секцию."""
        if not self.can_add_multicolumn(num_cols):
            return False
        # добавляем новую секцию с непрерывным разрывом
        section = self.document.add_section(WD_SECTION_START.CONTINUOUS)
        sectPr = section._sectPr

        # создаём элемент для колонок
        cols = OxmlElement('w:cols')
        cols.set(qn('w:num'), str(num_cols))
        cols.set(qn('w:space'), '720')  # отступ между колонками в twips (~1.27 см)
        cols.set(qn('w:equalWidth'), "1")  # равная ширина колонок
        sectPr.append(cols)

        # обновляем состояние
        self.current_columns = num_cols
        self.in_multicol = True
        self.elements_in_multicol = 0
        self.multicol_sections_added[str(num_cols)] = True
        # print(f"Начата многоколонная секция с {num_cols} колонками.")
        return True

    def end_multicolumn(self):
        """Заканчивает текущую многоколонную секцию."""
        if not self.in_multicol:
            return
        # добавляем новую секцию с непрерывным разрывом и одноколоночным режимом
        section = self.document.add_section(WD_SECTION_START.CONTINUOUS)
        sectPr = section._sectPr

        # устанавливаем одноколоночный режим
        cols = OxmlElement('w:cols')
        cols.set(qn('w:num'), '1')
        cols.set(qn('w:space'), '720')
        cols.set(qn('w:equalWidth'), "1")
        sectPr.append(cols)

        # обновляем состояние
        # print("Завершена многоколонная секция.")
        self.current_columns = 1
        self.in_multicol = False

    def can_start_multicolumn(self):
        """Проверяет, можно ли начать новую многоколонную секцию."""
        return (self.can_add_multicolumn(2) or self.can_add_multicolumn(3))


def set_section_orientation(section, orientation=WD_ORIENT.PORTRAIT):
    """Устанавливает ориентацию секции документа."""
    new_width, new_height = (section.page_height, section.page_width) if orientation == WD_ORIENT.LANDSCAPE else (section.page_width, section.page_height)
    section.orientation = orientation
    section.page_width = new_width
    section.page_height = new_height


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


def add_header_footer(document, header_text=None, footer_text=None):
    """Добавляет текст в колонтитулы документа."""
    section = document.sections[-1]
    if header_text:
        header = section.header
        header_para = header.paragraphs[0]
        header_para.text = header_text
        header_para.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.RIGHT
        ])
        header_para.runs[0].font.size = Pt(random.randint(12, 14))
        header_para.runs[0].font.bold = True
    if footer_text:
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = footer_text
        footer_para.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.RIGHT
        ])
        footer_para.runs[0].font.size = Pt(random.randint(10, 12))
        footer_para.runs[0].font.italic = True


def add_heading(document, level=2):
    """Добавляет заголовок заданного уровня в документ."""
    heading_text = fake.sentence(nb_words=6)
    p = document.add_heading(level=level).add_run(heading_text)
    p.font.size = Pt(random.randint(14 + (level -1)*2, 20 + (level -1)*2))
    if random.choice([True, False]):
        p.bold = True
    if random.choice([True, False]):
        p.italic = True
    heading_alignment = random.choice([
        WD_ALIGN_PARAGRAPH.LEFT,
        WD_ALIGN_PARAGRAPH.CENTER,
        WD_ALIGN_PARAGRAPH.RIGHT
    ])
    document.add_paragraph().paragraph_format.space_before = Pt(12)
    last_paragraph = document.paragraphs[-1]
    last_paragraph.alignment = heading_alignment
    # print(f"Добавлен заголовок уровня {level}: {heading_text}")


def add_text(document, doc_state, text, font_size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT):
    """Добавляет абзац текста в документ с заданным форматированием."""
    p = document.add_paragraph(text)
    run = p.runs[0]
    run.font.size = Pt(font_size)
    p.alignment = alignment
    # 50% шанс добавить красную строку
    if random.choice([True, False]):
        p.paragraph_format.first_line_indent = Cm(1.25)  # отступ первой строки
    else:
        p.paragraph_format.first_line_indent = Cm(0)
    # разнообразие межстрочного интервала
    p.paragraph_format.space_after = Pt(random.randint(6, 12))
    # print(f"Добавлен абзац текста: {text[:30]}...")


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
    # print(f"Добавлен нумерованный список с {num_items} элементами.")


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
    # print(f"Добавлен маркированный список с {num_items} элементами.")


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
        # print(f"Добавлена формула: {latex_formula}")
    except Exception as e:
        # в случае ошибки добавляем формулу как текст
        paragraph.add_run(latex_formula)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        # print(f"Ошибка при добавлении формулы: {e}. Добавлена как текст.")


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
    """Генерирует случайный график и сохраняет его во временный файл,
    учитывая режим колонок."""
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
    # print(f"Сгенерировано изображение: {image_path}")
    return image_path


def add_image(document, doc_state):
    """Добавляет изображение с подписью в документ, регулируя размер в зависимости от режима колонок."""
    pic_path = generate_random_plot_image(doc_state)
    if os.path.exists(pic_path):
        # устанавливаем ширину изображения в зависимости от режима колонок
        if doc_state.in_multicol:
            # для 2-х колонок: ширина ~4 см, для 3-х колонок: ~3 см
            if doc_state.current_columns == 2:
                img_width = Cm(4)
            elif doc_state.current_columns == 3:
                img_width = Cm(3)
            else:
                img_width = Inches(random.uniform(3, 6))
        else:
            img_width = min(Inches(random.uniform(4, 6)), Inches(6))  # максимальная ширина 6 дюймов
        
        # решаем, перед или после рисунка подписывать
        caption_before = random.choice([True, False])
        if caption_before:
            # подпись перед рисунком
            caption_text = f"Рис. {random.randint(1,100)}. {fake.sentence(nb_words=5)}"
            p = document.add_paragraph(caption_text, style='Caption')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].font.size = Pt(random.randint(10, 12))
            document.add_picture(pic_path, width=img_width)
        else:
            # подпись после рисунка
            document.add_picture(pic_path, width=img_width)
            caption_type = random.choice(['Рис. {num}. {text}', 'Рисунок {num} - {text}', 'Рисунок {num}'])
            num = random.randint(1, 100)
            if caption_type == 'Рисунок {num}':
                caption_text = f"Рисунок {num}"
            else:
                caption_text = caption_type.format(num=num, text=fake.sentence(nb_words=5))
            p = document.add_paragraph(caption_text, style='Caption')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].font.size = Pt(random.randint(10, 12))
        document.add_paragraph()
        # удаляем временный файл изображения
        os.remove(pic_path)
        # print(f"Добавлено изображение размером {img_width}.")


def add_footnote(paragraph, text, footnote_number):
    """Добавляет сноску в абзац."""
    run = paragraph.add_run(f"[{footnote_number}]")
    run.font.superscript = True
    run.font.size = Pt(8)
    paragraph.add_run(f" {text}")
    # print(f"Добавлена сноска [{footnote_number}]: {text}")


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
    # print("Добавлены концевые сноски.")


def add_table(document, doc_state):
    """Добавляет таблицу с подписью в документ, регуляируя размер в зависимости от режима колонок."""
    # добавление подписи к таблице
    caption_type = random.choice(['Табл. {num}. {text}', 'Таблица {num} - {text}', 'Таблица. {text}'])
    if 'num' in caption_type:
        table_num = random.randint(1, 100)
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

    # добавление таблицы
    table_styles = get_table_styles(document)
    num_rows = random.randint(5, 10)
    num_cols = random.randint(3, 6)

    # уменьшаем количество колонок для меньшего размера
    table = document.add_table(rows=num_rows, cols=num_cols)
    table.style = random.choice(table_styles) if table_styles else 'Table Grid'
    table.alignment = random.choice([
        WD_TABLE_ALIGNMENT.LEFT,
        WD_TABLE_ALIGNMENT.CENTER,
        WD_TABLE_ALIGNMENT.RIGHT
    ])

    # установка ширины таблицы
    if doc_state.in_multicol:
        if doc_state.current_columns == 2:
            table_width = Cm(12)  # примерная ширина для 2-х колонок
        elif doc_state.current_columns == 3:
            table_width = Cm(8)   # примерная ширина для 3-х колонок
        else:
            table_width = Cm(15)
    else:
        table_width = Cm(18)  # примерная ширина для одноколоночной секции
    table.autofit = False
    for row in table.rows:
        row.height = Pt(12)
    for idx, column in enumerate(table.columns):
        for cell in column.cells:
            cell.width = table_width / num_cols
            # очистим существующие параграфы в ячейке
            cell.text = ""

    # Выбор стиля таблицы
    table_style_option = random.choice(['random', 'single_color', 'alternating_color'])

    if table_style_option == 'random':
        # a) Абсолютно случайный стиль
        for row in table.rows:
            for cell in row.cells:
                if random.choice([True, False]):
                    fill_color = random.choice(colors_list)
                    shading_elm = OxmlElement('w:shd')
                    shading_elm.set(qn('w:val'), 'clear')
                    shading_elm.set(qn('w:color'), 'auto')
                    shading_elm.set(qn('w:fill'), fill_color)
                    cell._tc.get_or_add_tcPr().append(shading_elm)
                # Добавим случайный текст
                if random.choice([True, False]):
                    cell.text = fake.text(max_nb_chars=random.randint(5, 50))
                else:
                    cell.text = str(fake.random_number(digits=5))

    elif table_style_option == 'single_color':
        # b) Таблица с единым цветом фона
        single_color = random.choice(colors_list)
        for row in table.rows:
            for cell in row.cells:
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:val'), 'clear')
                shading_elm.set(qn('w:color'), 'auto')
                shading_elm.set(qn('w:fill'), single_color)
                cell._tc.get_or_add_tcPr().append(shading_elm)
                # Добавим случайный текст
                if random.choice([True, False]):
                    cell.text = fake.text(max_nb_chars=random.randint(5, 50))
                else:
                    cell.text = str(fake.random_number(digits=5))


    elif table_style_option == 'alternating_color':
        # c) Таблица с чередующимися цветами строк
        color_a, color_b = random.sample(colors_list, 2)
        for row_idx, row in enumerate(table.rows):
            row_color = color_a if row_idx % 2 == 0 else color_b
            for cell in row.cells:
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:val'), 'clear')
                shading_elm.set(qn('w:color'), 'auto')
                shading_elm.set(qn('w:fill'), row_color)
                cell._tc.get_or_add_tcPr().append(shading_elm)
                # Добавим случайный текст
                if random.choice([True, False]):
                    cell.text = fake.text(max_nb_chars=random.randint(5, 50))
                else:
                    cell.text = str(fake.random_number(digits=5))

    # Опционально: настройка выравнивания текста в ячейках
    for row in table.rows:
        for cell in row.cells:
            cell_paragraph = cell.paragraphs[0]
            cell_paragraph.alignment = random.choice([
                WD_ALIGN_PARAGRAPH.LEFT,
                WD_ALIGN_PARAGRAPH.CENTER,
                WD_ALIGN_PARAGRAPH.RIGHT,
                WD_ALIGN_PARAGRAPH.JUSTIFY
            ])
            # Настройка шрифта
            if cell_paragraph.runs:
                run = cell_paragraph.runs[0]
                run.font.size = Pt(random.randint(8, 12))

    # print(f"Добавлена таблица с {num_rows} строками и {num_cols} столбцами.")



def add_random_elements(document, doc_state, end_footnotes, generated_formulas):
    """
    Добавляет случайные элементы в документ в зависимости от текущего состояния колонки.
    """
    # определяем возможные элементы
    elements = ['heading', 'text', 'list', 'formula', 'image', 'footnote', 'table']
    if doc_state.in_multicol:
        # в многоколонной секции запрещаем добавлять таблицы
        elements.remove('table')
        weights = [10, 40, 10, 15, 15, 20]  # heading, text, list, formula, image, footnote
    else:
        weights = [10, 30, 10, 15, 15, 20, 10]  # heading, text, list, formula, image, footnote, table

    element_type = random.choices(
        elements,
        weights=weights,
        k=1
    )[0]

    # добавляем выбранный элемент
    if element_type == 'heading':
        level = random.choice([2, 3])
        add_heading(document, level=level)
    elif element_type == 'text':
        text = fake.paragraph(nb_sentences=random.randint(5, 15))
        font_size = random.randint(8, 16)
        alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.RIGHT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        add_text(document, doc_state, text, font_size, alignment)
    elif element_type == 'list':
        list_type = random.choice(['numbered', 'bulleted'])
        num_items = random.randint(3, 7)
        if list_type == 'numbered':
            add_numbered_list(document, num_items)
        else:
            add_bulleted_list(document, num_items)
    elif element_type == 'formula':
        add_formula(document, generated_formulas)
    elif element_type == 'image':
        add_image(document, doc_state)
    elif element_type == 'footnote':
        # решаем, добавлять ли сноску
        footnote_text = fake.sentence(nb_words=10)
        p = document.add_paragraph()
        add_footnote(p, footnote_text, len(end_footnotes) + 1)
        end_footnotes.append(footnote_text)
    elif element_type == 'table':
        add_table(document, doc_state)

    # увеличиваем счётчик элементов в многоколонной секции
    if doc_state.in_multicol:
        doc_state.elements_in_multicol += 1
        # если достигли лимита, прерываем многоколонную секцию
        if doc_state.elements_in_multicol >= doc_state.max_elements_multicol:
            doc_state.end_multicolumn()


def generate_document(doc_id, output_dir, num_iterations=100):
    """ Генерирует один документ с заданным количеством итераций добавления элементов. """
    document = Document()
    doc_state = DocumentState(document)

    # Устанавливаем ориентацию первой секции
    set_section_orientation(document.sections[-1], WD_ORIENT.PORTRAIT)

    # добавление колонтитулов
    header_text = fake.sentence(nb_words=4)
    footer_text = fake.sentence(nb_words=4)
    add_header_footer(document, header_text=header_text, footer_text=footer_text)
    end_footnotes = []
    generated_formulas = set()

    # начальная контент (одноколоночный)
    for _ in range(10):
        add_random_elements(document, doc_state, end_footnotes, generated_formulas)

    # основной цикл генерации контента
    for _ in range(num_iterations - 10):
        # решаем, вставлять ли новую секцию с возможным изменением ориентации
        if random.random() < 0.2:  # 20% шанс изменить ориентацию
            # выбираем ориентацию: 20% альбомная, 80% книжная
            orientation = WD_ORIENT.LANDSCAPE if random.random() < 0.25 else WD_ORIENT.PORTRAIT 

            # добавляем новую секцию
            section = document.add_section(WD_SECTION_START.NEW_PAGE)
            set_section_orientation(section, orientation)
            doc_state.current_orientation = orientation

        # решаем, вставлять ли многоколонную секцию
        if doc_state.can_start_multicolumn() and not doc_state.in_multicol:
            if random.random() < 0.05:  # 5% шанс начать многоколонную секцию
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
                            add_random_elements(document, doc_state, end_footnotes, generated_formulas)
                        # прерываем многоколонную секцию
                        doc_state.end_multicolumn()
                        continue  # переходим к следующей итерации

        # добавляем обычные элементы
        add_random_elements(document, doc_state, end_footnotes, generated_formulas)

    # проверка, чтобы документ не заканчивался многоколонной секцией
    if doc_state.in_multicol:
        doc_state.end_multicolumn()

    # добавляем концевые сноски
    add_document_end_footnotes(document, end_footnotes)

    # сохранение документа
    output_path = os.path.join(output_dir, f'demo_{doc_id}.docx')
    try:
        document.save(output_path)
        # print(f"Документ сохранён: {output_path}\n")
    except Exception as e:
        print(f"Ошибка при сохранении документа {output_path}: {e}")



def main():
    output_dir = 'C:/Users/ВИТАЛИЙ/Desktop/data/docx'
    os.makedirs(output_dir, exist_ok=True)
    num_docs = 3  # размер выборки, потом увеличим до 10000
    for doc_id in range(num_docs):
        # гарантируем, что многоколонные секции не будут на первой и последней страницах
        generate_document(doc_id, output_dir)
        if (doc_id + 1) % 100 == 0:
            print(f'Создано {doc_id + 1} документов')


if __name__ == "__main__":
    main()