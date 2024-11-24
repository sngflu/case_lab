import React from "react";
import { downloadZip, downloadJson } from "../api/api";

const DownloadButton = ({ onDownload }) => {
    const handleDownloadAll = async () => {
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
    };

    const handleDownloadJson = async () => {
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
    };

    return (
        <div>
            <button onClick={handleDownloadAll} className="page-button">Скачать все файлы</button>
            <button onClick={handleDownloadJson} className="page-button">Скачать JSON файлы</button>
        </div>
    );
};

export default DownloadButton;
