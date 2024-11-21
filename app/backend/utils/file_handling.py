import os
import shutil
from zipfile import ZipFile

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
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
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
    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
    return [os.path.join(extract_dir, f) for f in os.listdir(extract_dir) if f.endswith(".png")]

def clean_up(dirs: list):
    """
    Удаляет все временные файлы.

    Args:
        dirs (list): Список директорий для очистки.
    """
    for directory in dirs:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
