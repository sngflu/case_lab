import React from "react";
import { downloadZip } from "../api/api";

const DownloadButton = ({ onDownload }) => {
    const handleDownload = async () => {
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

    return <button onClick={handleDownload}>Скачать все файлы</button>;
};

export default DownloadButton;
