import os
import shutil
from zipfile import ZipFile

import pypdfium2 as pdfium
from fastapi import UploadFile

async def save_upload(file: UploadFile, upload_dir: str) -> str:
    """
    Сохраняет загруженный файл во временное хранилище.

    Args:
        file (UploadFile): Загружаемый файл.
        upload_dir (str): Директория для сохранения файла.

    Returns:
        str: Путь к сохраненному файлу.
    """
    # Формируем полный путь для сохранения файла
    filepath = os.path.join(upload_dir, file.filename)

    # Открываем файл для записи в бинарном режиме
    with open(filepath, "wb") as buffer:
        # Копируем содержимое загруженного файла в буфер
        shutil.copyfileobj(file.file, buffer)

    # Возвращаем путь к сохраненному файлу
    return filepath

def process_zip(zip_path: str, extract_dir: str) -> list:
    """
    Распаковывает ZIP-файл и возвращает список изображений.

    Args:
        zip_path (str): Путь к ZIP-файлу.
        extract_dir (str): Директория для распаковки файлов.

    Returns:
        list: Список путей к изображениям.
    """
    # Открываем ZIP-файл для чтения
    with ZipFile(zip_path, "r") as zip_ref:
        # Распаковываем все файлы из ZIP-архива в указанную директорию
        zip_ref.extractall(extract_dir)

    # Возвращаем список путей к изображениям с расширением .png
    return [os.path.join(extract_dir, f) for f in os.listdir(extract_dir) if f.endswith(".png")]

def pdf_to_images(pdf_path: str, img_dir: str, dpi=300) -> list:
    """
    Преобразует каждую страницу PDF-документа в изображение и сохраняет его в указанную директорию.

    Args:
        pdf_path (str): Путь к PDF-файлу.
        img_dir (str): Директория, в которую будут сохранены изображения.
        dpi (int, optional): Разрешение для рендеринга изображений в точках на дюйм.

    Returns:
        list: Список путей к сохраненным изображениям.
    """
    # Создаем директорию для сохранения изображений, если она не существует
    os.makedirs(img_dir, exist_ok=True)

    try:
        # Открываем PDF-документ
        pdf = pdfium.PdfDocument(pdf_path)
        img_paths = []

        # Итерируемся по каждой странице в PDF
        for i in range(len(pdf)):
            # Рендерим страницу в изображение
            page = pdf[i]
            img = page.render(scale=dpi / 72).to_pil()

            # Генерируем имя файла для изображения
            img_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_{i + 1}.png"
            img_path = os.path.join(img_dir, img_filename)

            # Сохраняем изображение в указанную директорию
            img.save(img_path)
            img_paths.append(img_path)

        # Возвращаем список путей к изображениям
        return img_paths

    except Exception as e:
        # Выводим сообщение об ошибке, если произошло исключение
        print(f"Ошибка при обработке {pdf_path}: {e}")
        return []

def clean_up(dirs: list) -> None:
    """
    Удаляет все временные файлы.

    Args:
        dirs (list): Список директорий для очистки.
    """
    # Итерируемся по каждой директории в списке
    for directory in dirs:
        # Итерируемся по каждому файлу в директории
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)

            # Удаляем файл или символическую ссылку
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            # Удаляем директорию и все её содержимое
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
