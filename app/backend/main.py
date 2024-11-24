# src/backend/main.py
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
from utils.file_handling import save_upload, clean_up

app = FastAPI()

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

MODEL_WEIGHTS = "model/best.pt"
yolo_model = load_model(MODEL_WEIGHTS)

UPLOAD_DIR = "data/uploads"
RESULT_DIR = "data/results"
JSON_DIR = "data/json"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

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

    for file in files:
        input_path = await save_upload(file, UPLOAD_DIR)
        output_path = os.path.join(RESULT_DIR, f"annotated_{file.filename}")
        json_path = os.path.join(JSON_DIR, f"annotated_{file.filename}.json")

        results = yolo_model.predict(input_path)

        image = Image.open(input_path)
        image_height, image_width = image.size

        json_annotation = yolo_model.create_json_annotation(input_path, image_height, image_width, results)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_annotation, f, ensure_ascii=False, indent=4)

        yolo_model.annotate_image(input_path, results, output_path)
        processed_files.append(output_path)
        json_files.append(json_path)

    return {"filenames": [os.path.basename(file) for file in processed_files], "json_filenames": [os.path.basename(file) for file in json_files]}

@app.get("/download/pics")
async def download_results():
    """
    Создает ZIP-архив с обработанными изображениями и возвращает его для скачивания.

    Returns:
        FileResponse: Ответ с ZIP-архивом.
    """
    zip_path = os.path.join(RESULT_DIR, "processed_images.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(RESULT_DIR):
            file_path = os.path.join(RESULT_DIR, file)
            if file.endswith(".png"):
                zipf.write(file_path, arcname=file)

    return FileResponse(zip_path, media_type="application/zip", filename="processed_images.zip")

@app.get("/download/json/")
async def download_json():
    """
    Создает ZIP-архив с JSON-файлами и возвращает его для скачивания.

    Returns:
        FileResponse: Ответ с ZIP-архивом.
    """
    zip_path = os.path.join(JSON_DIR, "processed_json.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in os.listdir(JSON_DIR):
            file_path = os.path.join(JSON_DIR, file)
            if file.endswith(".json"):
                zipf.write(file_path, arcname=file)

    return FileResponse(zip_path, media_type="application/zip", filename="processed_json.zip")

@app.post("/cleanup/")
async def cleanup():
    """
    Очищает директории с загруженными и обработанными файлами.

    Returns:
        dict: Сообщение об успешной очистке.
    """
    clean_up([UPLOAD_DIR, RESULT_DIR, JSON_DIR])
    return {"message": "Директории очищены"}
