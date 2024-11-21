import os
import zipfile
import logging
from typing import List

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
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

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
    logging.info(f"Получено {len(files)} файлов")
    processed_files = []

    for file in files:
        input_path = await save_upload(file, UPLOAD_DIR)
        output_path = os.path.join(RESULT_DIR, f"annotated_{file.filename}")

        results = yolo_model.predict(input_path)

        yolo_model.annotate_image(input_path, results, output_path)
        processed_files.append(output_path)

    return {"filenames": [os.path.basename(file) for file in processed_files]}

@app.get("/download/")
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

@app.post("/cleanup/")
async def cleanup():
    """
    Очищает директории с загруженными и обработанными файлами.

    Returns:
        dict: Сообщение об успешной очистке.
    """
    clean_up([UPLOAD_DIR, RESULT_DIR])
    return {"message": "Директории очищены"}
