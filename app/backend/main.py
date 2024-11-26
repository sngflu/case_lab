import os
import zipfile
from typing import List
from PIL import Image
import json

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from model.model import load_model
from utils.file_handling import save_upload, clean_up, pdf_to_images

# Создаем экземпляр FastAPI
app = FastAPI()

# Настройка CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь к весам модели
MODEL_WEIGHTS = "model/best_model.pt"
# Загружаем модель
yolo_model = load_model(MODEL_WEIGHTS)

# Директории для загрузки, результатов и JSON-файлов
UPLOAD_DIR = "data/uploads"
RESULT_DIR = "data/results"
JSON_DIR = "data/json"

# Создаем директории, если они не существуют
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# Монтируем статические файлы
app.mount("/results", StaticFiles(directory="data/results"), name="results")

@app.post("/process/")
async def process_images(files: List[UploadFile] = File(...)):
    """
    Обрабатывает загруженные изображения и сохраняет аннотированные результаты.

    Args:
        files (List[UploadFile]): Список загруженных файлов.

    Returns:
        dict: Словарь с именами обработанных файлов.
    """
    processed_files = []
    json_files = []

    # Обрабатываем каждый загруженный файл
    for file in files:
        # Сохраняем загруженный файл
        input_path = await save_upload(file, UPLOAD_DIR)

        # Если файл является PDF
        if file.filename.lower().endswith('.pdf'):
            # Создаем директорию для изображений из PDF
            img_dir = os.path.join(UPLOAD_DIR, os.path.splitext(file.filename)[0])
            # Преобразуем PDF в изображения
            img_paths = pdf_to_images(input_path, img_dir)

            # Обрабатываем каждое изображение из PDF
            for img_path in img_paths:
                # Путь для сохранения аннотированного изображения
                output_path = os.path.join(RESULT_DIR, f"annotated_{os.path.basename(img_path)}")
                # Путь для сохранения JSON-аннотации
                json_path = os.path.join(JSON_DIR, f"annotated_{os.path.basename(img_path)}.json")

                # Получаем результаты предсказания модели
                results = yolo_model.predict(img_path)

                # Открываем изображение для получения его размеров
                image = Image.open(img_path)
                image_height, image_width = image.size

                # Создаем JSON-аннотацию
                json_annotation = yolo_model.create_json_annotation(img_path, image_height, image_width, results)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_annotation, f, ensure_ascii=False, indent=4)

                # Аннотируем изображение
                yolo_model.annotate_image(img_path, results, output_path)
                processed_files.append(output_path)
                json_files.append(json_path)
        else:
            # Путь для сохранения аннотированного изображения
            output_path = os.path.join(RESULT_DIR, f"annotated_{file.filename}")
            # Путь для сохранения JSON-аннотации
            json_path = os.path.join(JSON_DIR, f"annotated_{file.filename}.json")

            # Получаем результаты предсказания модели
            results = yolo_model.predict(input_path)

            # Открываем изображение для получения его размеров
            image = Image.open(input_path)
            image_height, image_width = image.size

            # Создаем JSON-аннотацию
            json_annotation = yolo_model.create_json_annotation(input_path, image_height, image_width, results)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_annotation, f, ensure_ascii=False, indent=4)

            # Аннотируем изображение
            yolo_model.annotate_image(input_path, results, output_path)
            processed_files.append(output_path)
            json_files.append(json_path)

    # Возвращаем список имен обработанных файлов и JSON-файлов
    return {"filenames": [os.path.basename(file) for file in processed_files], "json_filenames": [os.path.basename(file) for file in json_files]}

@app.get("/download/pics")
async def download_results():
    """
    Создает ZIP-архив с обработанными изображениями и возвращает его для скачивания.

    Returns:
        FileResponse: Ответ с ZIP-архивом.
    """
    # Путь для сохранения ZIP-архива
    zip_path = os.path.join(RESULT_DIR, "processed_images.zip")

    # Создаем ZIP-архив с обработанными изображениями
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(RESULT_DIR):
            file_path = os.path.join(RESULT_DIR, file)
            if file.endswith(".png"):
                zipf.write(file_path, arcname=file)

    # Возвращаем ZIP-архив для скачивания
    return FileResponse(zip_path, media_type="application/zip", filename="processed_images.zip")

@app.get("/download/json/")
async def download_json():
    """
    Создает ZIP-архив с JSON-файлами и возвращает его для скачивания.

    Returns:
        FileResponse: Ответ с ZIP-архивом.
    """
    # Путь для сохранения ZIP-архива
    zip_path = os.path.join(JSON_DIR, "processed_json.zip")

    # Создаем ZIP-архив с JSON-файлами
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(JSON_DIR):
            file_path = os.path.join(JSON_DIR, file)
            if file.endswith(".json"):
                zipf.write(file_path, arcname=file)

    # Возвращаем ZIP-архив для скачивания
    return FileResponse(zip_path, media_type="application/zip", filename="processed_json.zip")

@app.post("/cleanup/")
async def cleanup():
    """
    Очищает директории с загруженными и обработанными файлами.

    Returns:
        dict: Сообщение об успешной очистке.
    """
    # Очищаем директории
    clean_up([UPLOAD_DIR, RESULT_DIR, JSON_DIR])
    return {"message": "Директории очищены"}
