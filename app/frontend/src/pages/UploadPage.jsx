import React, { useState } from "react";
import FileUploader from "../components/FileUploader";
import { useNavigate } from 'react-router-dom';

/**
 * Компонент страницы загрузки файлов.
 *
 * @param {Function} onProcessingComplete - Функция обратного вызова, вызываемая после завершения обработки файлов.
 * @returns {JSX.Element} - Компонент страницы загрузки файлов.
 */
const UploadPage = ({ onProcessingComplete }) => {
    // Состояние для хранения обработанных файлов
    const [processedFiles, setProcessedFiles] = useState([]);
    // Хук для навигации
    const navigate = useNavigate();

    /**
     * Обрабатывает загрузку файлов.
     *
     * @param {Array} files - Массив обработанных файлов.
     */
    const handleUpload = (files) => {
        console.log("Uploading files:", files);
        // Обновляем состояние обработанных файлов
        setProcessedFiles(files);
        // Вызываем функцию обратного вызова после завершения обработки файлов
        onProcessingComplete(files);
        // Переходим на страницу результатов
        navigate('/results');
    };

    return (
        <div>
            {/* Компонент для загрузки файлов */}
            <FileUploader onUpload={handleUpload} />
            {/* Отображение предпросмотра обработанных файлов, если они есть */}
            {processedFiles.length > 0 && <Preview files={processedFiles} />}
        </div>
    );
};

export default UploadPage;
