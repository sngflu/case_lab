import React from "react";
import { downloadZip, downloadJson } from "../api/api";

/**
 * Компонент кнопки для скачивания файлов.
 *
 * @param {Function} onDownload - Функция обратного вызова, вызываемая после завершения скачивания.
 * @returns {JSX.Element} - Компонент кнопки для скачивания файлов.
 */
const DownloadButton = ({ onDownload }) => {
    /**
     * Обрабатывает скачивание файлов.
     */
    const handleDownloadAll = async () => {
        try {
            const response = await downloadZip();

            if (!response.data) {
                console.error("Ответ от API не содержит данных.");
                alert("Не удалось скачать файлы.");
                return;
            }

            const blob = new Blob([response.data], { type: "application/zip" });
            const link = document.createElement("a");
            link.href = window.URL.createObjectURL(blob);
            link.download = "processed_images.zip";
            link.click();
            onDownload();
        } catch (error) {
            console.error("Ошибка при скачивании файлов:", error);
            alert("Произошла ошибка при скачивании файлов.");
        }
    };

    /**
     * Обрабатывает скачивание JSON файлов.
     */
    const handleDownloadJson = async () => {
        try {
            const response = await downloadJson();

            if (!response.data) {
                console.error("Ответ от API не содержит данных.");
                alert("Не удалось скачать JSON файлы.");
                return;
            }

            const blob = new Blob([response.data], { type: "application/zip" });
            const link = document.createElement("a");
            link.href = window.URL.createObjectURL(blob);
            link.download = "processed_json.zip";
            link.click();
            onDownload();
        } catch (error) {
            console.error("Ошибка при скачивании JSON файлов:", error);
            alert("Произошла ошибка при скачивании JSON файлов.");
        }
    };

    return (
        <div>
            <button onClick={handleDownloadAll} className="page-button">Скачать все файлы</button>
            <button onClick={handleDownloadJson} className="page-button">Скачать JSON файлы</button>
        </div>
    );
};

export default DownloadButton;
