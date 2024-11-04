import random
import os
import uuid
import tempfile
from collections import OrderedDict
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import RGBColor, Pt, Inches, Cm
from faker import Faker
from mimesis import Generic
from mimesis.locales import Locale
from mimesis.builtins import RussiaSpecProvider
import matplotlib.pyplot as plt

# настройка Faker и Mimesis
fake = Faker(['ru-RU', 'en-US'])
generic = Generic(locale=Locale.RU, seed=42)
generic.add_provider(RussiaSpecProvider)

# константы COLORS
COLORS = """000000 000080 00008B 0000CD 0000FF 006400 008000 008080 008B8B 00BFFF 00CED1 00FA9A 
00FF00 00FF7F 00FFFF 191970 1E90FF 20B2AA 228B22 2E8B57 2F4F4F 32CD32 3CB371 40E0E0 
4169E1 4682B4 483D8B 48D1CC 4B0082 556B2F 5F9EA0 6495ED 66CDAA 696969 6A5ACD 6B8E23 
708090 778899 7B68EE 7CFC00 7FFF00 7FFFD4 800000 800080 808000 808080 87CEEB 87CEFA 
8A2BE2 8B0000 8B008B 8B4513 8FBC8F 90EE90 9370D8 9400D3 98FB98 9932CC 9ACD32 A0522D 
A52A2A A9A9A9 ADD8E6 ADFF2F AFEEEE B0C4DE B0E0E6 B22222 B8860B BA55D3 BC8F8F BDB76B 
C0C0C0 C71585 CD5C5C CD853F D2691E D2B48C D3D3D3 D87093 D8BFD8 DA70D6 DAA520 DC143C 
DCDCDC DDA0DD DEB887 E0FFFF E6E6FA E9967A EE82EE EEE8AA F08080 F0E68C F0F8FF F0FFF0 
F0FFFF F4A460 F5DEB3 F5F5DC F5F5F5 F5FFFA F8F8FF FA8072 FAEBD7 FAF0E6 FAFAD2 FDF5E6 
FF0000 FF00FF FF00FF FF1493 FF4500 FF6347 FF69B4 FF7F50 FF8C00 FFA07A FFA500 FFB6C1 
FFC0CB FFD700 FFDAB9 FFDEAD FFE4B5 FFE4C4 FFE4E1 FFEBCD FFEFD5 FFF0F5 FFF5EE FFF8DC 
FFFA-CD FFFAF0 FFFAFA FFFF00 FFFFE0 FFFFF0 FFFFFF"""
colors_list = COLORS.split()

locales = OrderedDict([
    ('en-US', 1),
    ('ru-RU', 2),
])

# еласс для отслеживания состояния документа
class DocumentState:
    def __init__(self, document):
        self.current_columns = 1
        self.document = document
        self.section_width = self.calculate_section_width()
        # ограничение: максимум 1 секция с 2 колонками и 1 с 3 колонками
        self.multicolumn_sections = {'2': False, '3': False}
    
    def set_columns(self, num_cols):
        self.current_columns = num_cols
        self.section_width = self.calculate_section_width()
    
    def calculate_section_width(self):
        # получаем текущую секцию
        section = self.document.sections[-1]
        page_width = section.page_width
        left_margin = section.left_margin
        right_margin = section.right_margin
        # вычисляем доступную ширину
        usable_width = page_width - left_margin - right_margin
        # вычисляем ширину одной колонки с отступом
        space_between = Cm(1.27)  # 720 twips ≈ 1.27 см
        total_space = space_between if self.current_columns > 1 else 0
        column_width = (usable_width - total_space) / self.current_columns
        return column_width
    
    def can_add_multicolumn(self, num_cols):
        if num_cols == 2 and not self.multicolumn_sections['2']:
            return True
        elif num_cols == 3 and not self.multicolumn_sections['3']:
            return True
        else:
            return False
    
    def mark_multicolumn_added(self, num_cols):
        if num_cols == 2:
            self.multicolumn_sections['2'] = True
        elif num_cols == 3:
            self.multicolumn_sections['3'] = True

def get_table_styles(document):
    styles = document.styles
    table_styles = []
    table = document.add_table(rows=1, cols=1)
    for s in styles:
        if 'Table' in s.name or 'Таблица' in s.name:
            try:
                table.style = s
                table_styles.append(s.name)
            except:
                pass
    # удаляем временную таблицу
    table._element.getparent().remove(table._element)
    return table_styles

def change_orientation(document):
    current_section = document.sections[-1]
    if random.choice([True, False]):
        current_section.orientation = WD_ORIENT.LANDSCAPE
        new_width, new_height = current_section.page_height, current_section.page_width
        current_section.page_width = new_width
        current_section.page_height = new_height

def add_header_footer(document, header_text=None, footer_text=None):
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
        header_para.runs[0].font.size = Pt(random.randint(8, 12))
    if footer_text:
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = footer_text
        footer_para.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.RIGHT
        ])
        footer_para.runs[0].font.size = Pt(random.randint(8, 12))

def add_numbered_list(document, num_items=5):
    for _ in range(num_items):
        p = document.add_paragraph(fake.sentence(nb_words=6), style='List Number')
        p.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.RIGHT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        p.runs[0].font.size = Pt(random.randint(8, 16))
        # установка отступа и межстрочного интервала
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.space_after = Pt(6)

def add_bulleted_list(document, num_items=5):
    for _ in range(num_items):
        p = document.add_paragraph(fake.sentence(nb_words=6), style='List Bullet')
        p.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.RIGHT,
            WD_ALIGN_PARAGRAPH.JUSTIFY
        ])
        p.runs[0].font.size = Pt(random.randint(8, 16))
        # установка отступа и межстрочного интервала
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.space_after = Pt(6)

def add_multicolumn_section(document, doc_state):
    # проверяем, можно ли добавить секцию с 2 или 3 колонками
    possible_columns = []
    if not doc_state.multicolumn_sections['2']:
        possible_columns.append(2)
    if not doc_state.multicolumn_sections['3']:
        possible_columns.append(3)
    
    if not possible_columns:
        return  # нет возможности добавить больше многоколонных секций
    
    # выбираем случайное количество колонок из доступных
    num_cols = random.choice(possible_columns)
    
    # добавляем раздел с многоколоночным оформлением без перехода на новую страницу
    sect = document.add_section(WD_SECTION.NEW_PAGE)
    sectPr = sect._sectPr
    
    # создаём элемент для колонок
    cols = OxmlElement('w:cols')
    cols.set(qn('w:num'), str(num_cols))
    cols.set(qn('w:space'), '720')  # 720 twips ≈ 1.27 см
    cols.set(qn('w:equalWidth'), "1")  # колонки равной ширины
    sectPr.append(cols)
    
    # обновляем состояние документа
    doc_state.set_columns(num_cols)
    doc_state.mark_multicolumn_added(num_cols)
    
    return sect

def generate_random_plot_image():
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
    
    # сохраняем изображение во временный файл
    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4()
    image_path = os.path.join(temp_dir, f"plot_{unique_id}.png")
    plt.savefig(image_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    return image_path

def add_page_footnote(paragraph, text, footnote_number):
    """Добавляет постраничную сноску в параграф."""
    # добавляем номер сноски
    run = paragraph.add_run(f"[{footnote_number}]")
    run.font.superscript = True
    run.font.size = Pt(8)
    
    # добавляем текст сноски как обычный текст (имитация постраничной сноски)
    paragraph.add_run(f" {text}")

def add_document_end_footnotes(document, end_footnotes):
    """Добавляет список концевых сносок в конце документа."""
    if not end_footnotes:
        return
    # добавляем раздел перед концевыми сносками, если текущая секция многоколонная
    current_section = document.sections[-1]
    cols = current_section._sectPr.xpath('.//w:cols')
    is_multicol = False
    if cols:
        num_cols = int(cols[0].get(qn('w:num'), '1'))
        is_multicol = num_cols > 1
    
    if is_multicol:
        # добавляем раздел для концевых сносок в одноколоночной секции
        document.add_section(WD_SECTION.NEW_PAGE)
    
    p = document.add_paragraph("Концевые сноски", style='Heading 2')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].font.size = Pt(random.randint(14, 22))
    for idx, footnote in enumerate(end_footnotes, 1):
        p = document.add_paragraph(f"{idx}. {footnote}", style='Normal')
        p.runs[0].font.size = Pt(random.randint(8, 14))
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

def add_formula(document):
    """Добавляет сгенерированную формулу как Office Math объект в документ."""
    omml_para = generate_formula_omml()
    if omml_para is None:
        return  # если формула не сгенерирована, не добавляем
    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    # вставляем OMML в run
    run._r.append(omml_para)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

def generate_formula_omml():
    """Генерирует простую OMML формулу (полином или дробь) с правильной структурой."""
    formula_type = random.choice(['polynomial', 'fraction'])
    
    if formula_type == 'polynomial':
        degree = random.randint(2, 4)
        coefficients = [random.randint(-5, 5) for _ in range(degree + 1)]
        # убедимся, что хотя бы один коэффициент не равен нулю
        if all(coef == 0 for coef in coefficients):
            coefficients[random.randint(0, degree)] = random.randint(1, 5)
        # построение уравнения
        terms = []
        for i, coef in enumerate(coefficients):
            power = degree - i
            if coef == 0:
                continue
            sign = '-' if coef < 0 else '+'
            abs_coef = abs(coef)
            if power > 1:
                term = f"{abs_coef}x^{power}"
            elif power == 1:
                term = f"{abs_coef}x"
            else:
                term = f"{abs_coef}"
            if terms:
                terms.append(f" {sign} {term}")
            else:
                if coef < 0:
                    terms.append(f"- {term}")
                else:
                    terms.append(f"{term}")
        equation = ''.join(terms) if terms else '0'
    
        # создаём OMML строку
        math_xml = f'''
        <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
            <m:oMath>
                <m:r>
                    <m:t>{equation}</m:t>
                </m:r>
            </m:oMath>
        </m:oMathPara>
        '''
        try:
            omml_para = parse_xml(math_xml)
            return omml_para
        except Exception as e:
            print(f"Ошибка при генерации OMML полинома: {e}")
            return None
    
    elif formula_type == 'fraction':
        # генерация дроби вида (ax + b)/(cx + d)
        a = random.randint(1, 10)
        b = random.randint(-10, 10)
        c = random.randint(1, 10)
        d = random.randint(-10, 10)
    
        numerator = f"{a}x"
        if b != 0:
            numerator += f" {'+' if b > 0 else '-'} {abs(b)}"
    
        denominator = f"{c}x"
        if d != 0:
            denominator += f" {'+' if d > 0 else '-'} {abs(d)}"
    
        # cоздаём OMML строку для дроби
        math_xml = f'''
        <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
            <m:oMath>
                <m:f>
                    <m:num>
                        <m:r>
                            <m:t>{numerator}</m:t>
                        </m:r>
                    </m:num>
                    <m:den>
                        <m:r>
                            <m:t>{denominator}</m:t>
                        </m:r>
                    </m:den>
                </m:f>
            </m:oMath>
        </m:oMathPara>
        '''
        try:
            omml_para = parse_xml(math_xml)
            return omml_para
        except Exception as e:
            print(f"Ошибка при генерации OMML дроби: {e}")
            return None
    else:
        return None

def add_random_elements(document, doc_state, end_footnotes):
    """Добавляет случайные элементы в документ."""
    # Проверяем, является ли текущая секция многоколонной
    current_section = document.sections[-1]
    cols = current_section._sectPr.xpath('.//w:cols')
    is_multicol = False
    if cols:
        num_cols = int(cols[0].get(qn('w:num'), '1'))
        is_multicol = num_cols > 1
    
    # eсли текущая секция многоколонная, добавляем только текст
    if is_multicol:
        # Добавление абзаца с текстом
        para_text = fake.text(max_nb_chars=random.randint(500, 1000))
        p = document.add_paragraph(para_text)
        p.style = 'Normal'
        p.alignment = random.choice([
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
            WD_ALIGN_PARAGRAPH.RIGHT,
            WD_ALIGN_PARAGRAPH.CENTER
        ])
        run = p.runs[0]
        run.font.size = Pt(random.randint(8, 16))
        # случайно добавляем отступ первой строки
        if random.choice([True, False]):
            p.paragraph_format.first_line_indent = Cm(1.25)  # стандартный отступ первой строки
        
        # добавление сноски
        if random.choice([True, False]):
            footnote_text = fake.sentence(nb_words=10)
            # асегда считаем это концевой сноской
            end_footnotes.append(footnote_text)
            # добавляем маркер сноски в текст
            footnote_number = len(end_footnotes)
            run = p.add_run(f"[{footnote_number}]")
            run.font.superscript = True
            run.font.size = Pt(8)
        
        # добавление формулы
        if random.choice([True, False]):
            add_formula(document)
        
        return
    
    # иначе, если секция одноколоночная, добавляем разные элементы
    # добавление заголовка
    p = document.add_paragraph(fake.sentence(nb_words=6))
    heading_level = random.randint(1, 3)
    p.style = f'Heading {heading_level}'
    run = p.runs[0]
    run.bold = bool(random.getrandbits(1))
    run.italic = bool(random.getrandbits(1))
    run.font.size = Pt(random.randint(14, 22))
    p.alignment = random.choice([
        WD_ALIGN_PARAGRAPH.LEFT,
        WD_ALIGN_PARAGRAPH.CENTER,
        WD_ALIGN_PARAGRAPH.RIGHT
    ])
    
    # добавление подписи к таблице
    caption_type = random.choice(['table_with_num', 'table_no_num'])
    table_num = random.randint(1, 100)
    if caption_type == 'table_with_num':
        caption_text = f"Таблица {table_num}. {fake.sentence(nb_words=4)}"
    else:
        caption_text = f"Таблица. {fake.sentence(nb_words=4)}"
    p = document.add_paragraph(caption_text, style='Caption')
    run = p.runs[0]
    run.italic = True
    run.font.size = Pt(12)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    # добавление таблицы
    table_styles = get_table_styles(document)
    table = document.add_table(rows=random.randint(5, 10), cols=random.randint(3, 8))
    table.style = random.choice(table_styles) if table_styles else 'Table Grid'
    table.alignment = random.choice([
        WD_TABLE_ALIGNMENT.LEFT,
        WD_TABLE_ALIGNMENT.CENTER,
        WD_TABLE_ALIGNMENT.RIGHT
    ])
    for row in table.rows:
        for cell in row.cells:
            if random.randint(0, 3) > 2:
                cell.text = fake.text(max_nb_chars=random.randint(5, 50))
            else:
                cell.text = str(fake.random_number(digits=5))
            # установка выравнивания внутри ячейки
            cell_paragraph = cell.paragraphs[0]
            cell_paragraph.alignment = random.choice([
                WD_ALIGN_PARAGRAPH.LEFT,
                WD_ALIGN_PARAGRAPH.CENTER,
                WD_ALIGN_PARAGRAPH.RIGHT,
                WD_ALIGN_PARAGRAPH.JUSTIFY
            ])
            # установка цвета фона ячейки
            fill_color = random.choice(colors_list)
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:val'), 'clear')
            shading_elm.set(qn('w:color'), 'auto')
            shading_elm.set(qn('w:fill'), fill_color)
            cell._tc.get_or_add_tcPr().append(shading_elm)
    
    # добавление абзаца с возможным отступом первой строки
    para_text = fake.text(max_nb_chars=random.randint(500, 1000))
    p = document.add_paragraph(para_text)
    p.style = 'Normal'
    p.alignment = random.choice([
        WD_ALIGN_PARAGRAPH.LEFT,
        WD_ALIGN_PARAGRAPH.JUSTIFY,
        WD_ALIGN_PARAGRAPH.RIGHT,
        WD_ALIGN_PARAGRAPH.CENTER
    ])
    run = p.runs[0]
    run.font.size = Pt(random.randint(8, 16))
    # случайно добавляем отступ первой строки
    if random.choice([True, False]):
        p.paragraph_format.first_line_indent = Cm(1.25)  # Стандартный отступ первой строки
    
    # добавление сноски
    if random.choice([True, False]):
        footnote_text = fake.sentence(nb_words=10)
        # решаем тип сноски
        footnote_type = random.choice(['page', 'end'])
        if footnote_type == 'page':
            # постраничная сноска
            footnote_number = len(end_footnotes) + 1
            add_page_footnote(p, footnote_text, footnote_number)
        else:
            # концевая сноска
            end_footnotes.append(footnote_text)
            # добавляем маркер сноски в текст
            footnote_number = len(end_footnotes)
            run = p.add_run(f"[{footnote_number}]")
            run.font.superscript = True
            run.font.size = Pt(8)
    
    # добавление формулы
    if random.choice([True, False]):
        add_formula(document)
    
    # добавление списков
    if random.choice([True, False]):
        add_numbered_list(document, num_items=random.randint(3, 7))
    if random.choice([True, False]):
        add_bulleted_list(document, num_items=random.randint(3, 7))
    
    # добавление рисунка (опционально) с случайной позицией подписей
    if random.choice([True, False]):
        # генерация случайного графика
        pic_path = generate_random_plot_image()
        if os.path.exists(pic_path):
            # подбор ширины изображения на основе текущего количества колонок
            if doc_state.current_columns > 1:
                column_width_in_inches = doc_state.section_width / Cm(1) * 0.393700787  # Конвертируем cm в inches
                img_width = min(column_width_in_inches * 0.8, Inches(6))  # 80% ширины колонки или максимум 6 дюймов
            else:
                img_width = min(Inches(random.uniform(3, 6)), Inches(6))
            # случайно решаем, перед или после рисунка
            if random.choice([True, False]):
                # подпись перед рисунком
                caption_text = f"Рисунок {random.randint(1,100)}. {fake.sentence(nb_words=5)}"
                p = document.add_paragraph(caption_text, style='Caption')
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.runs[0].font.size = Pt(12)
                document.add_picture(pic_path, width=img_width)
            else:
                # подпись после рисунка
                document.add_picture(pic_path, width=img_width)
                caption_text = f"Рисунок {random.randint(1,100)}. {fake.sentence(nb_words=5)}"
                p = document.add_paragraph(caption_text, style='Caption')
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.runs[0].font.size = Pt(12)
            # удаляем временный файл изображения
            os.remove(pic_path)

def generate_document(doc_id, output_dir, num_iterations=10):
    """Генерирует один документ с заданным количеством итераций добавления элементов."""
    document = Document()
    # история состояния документа
    doc_state = DocumentState(document)
    # добавление колонтитулов
    header_text = fake.sentence(nb_words=4)
    footer_text = fake.sentence(nb_words=4)
    add_header_footer(document, header_text=header_text, footer_text=footer_text)
    # список для концевых сносок
    end_footnotes = []
    # ылаг для того, чтобы добавить завершающую одноколоночную секцию
    need_final_single_column = False
    
    for _ in range(num_iterations):
        change_orientation(document)
        # решение о многоколоночном разделе (~20% вероятность)
        add_section = random.choices(
            [True, False],
            weights=[2, 8],  # примерно 20% вероятность
            k=1
        )[0]
        if add_section and (doc_state.multicolumn_sections['2'] == False or doc_state.multicolumn_sections['3'] == False):
            add_multicolumn_section(document, doc_state)
            need_final_single_column = True  # после многоколонной секции нужна одноколоночная
        
        # добавление различных элементов
        add_random_elements(document, doc_state, end_footnotes)
        
        # если была добавлена секция с колонками, следующая секция должна быть одноколоночной
        if need_final_single_column:
            # добавляем новую секцию чтобы вернуться к одноколоночному содержимому
            document.add_section(WD_SECTION.NEW_PAGE)
            need_final_single_column = False

    # добавление завершающей секции, если документ заканчивается многоколонным текстом
    current_section = document.sections[-1]
    cols = current_section._sectPr.xpath('.//w:cols')
    is_multicol = False
    if cols:
        num_cols = int(cols[0].get(qn('w:num'), '1'))
        is_multicol = num_cols > 1
    if is_multicol:
        document.add_section(WD_SECTION.NEW_PAGE)

    # добавление концевых сносок в конце документа
    add_document_end_footnotes(document, end_footnotes)
    
    # сохранение документа
    output_path = os.path.join(output_dir, f'demo_{doc_id}.docx')
    try:
        document.save(output_path)
    except Exception as e:
        print(f"Ошибка при сохранении документа {output_path}: {e}")

def main():
    output_dir = './data/docx'  # чтобы было верно, надо выполнять из корневого каталога проекта
    os.makedirs(output_dir, exist_ok=True)
    num_docs = 10  # размер выборки, надо будет поменять до 10 000
    for doc_id in range(num_docs):
        generate_document(doc_id, output_dir)
        if (doc_id + 1) % 100 == 0:
            print(f'Создано {doc_id + 1} документов')

if __name__ == "__main__": 
    main()