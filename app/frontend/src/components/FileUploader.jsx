import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadFiles } from "../api/api";
import Preview from "../components/Preview";

/**
 * Компонент для загрузки файлов.
 *
 * @param {Function} onUpload - Функция обратного вызова, вызываемая после завершения загрузки.
 * @returns {JSX.Element} - Компонент для загрузки файлов.
 */
const FileUploader = ({ onUpload }) => {
    // Состояние для хранения выбранных файлов
    const [selectedFiles, setSelectedFiles] = useState([]);
    // Состояние для отслеживания процесса загрузки
    const [uploading, setUploading] = useState(false);

    /**
     * Обрабатывает перетаскивание файлов.
     *
     * @param {File[]} acceptedFiles - Массив принятых файлов.
     */
    const onDrop = useCallback((acceptedFiles) => {
        // Создаем массив файлов с превью
        const newFilesWithPreviews = acceptedFiles.map(file => {
            const previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : null;
            console.log(`File: ${file.name}, Preview URL: ${previewUrl}`);
            return {
                file,
                url: previewUrl,
                name: file.name,
            };
        });

        // Обновляем состояние выбранных файлов
        setSelectedFiles(prevFiles => [...prevFiles, ...newFilesWithPreviews]);
    }, []);

    // Настройки для useDropzone
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            "image/png": [],
            "image/jpeg": [],
            "image/jpg": [],
            "application/pdf": [],
        },
        multiple: true,
    });

    /**
     * Обрабатывает загрузку файлов на сервер.
     */
    const handleFileUpload = async () => {
        if (selectedFiles.length === 0) return;

        const formData = new FormData();
        selectedFiles.forEach(file => formData.append("files", file.file));

        setUploading(true);
        try {
            const response = await uploadFiles(formData);
            if (response.data && Array.isArray(response.data.filenames)) {
                onUpload(response.data.filenames);
            } else {
                alert("Ошибка обработки файлов");
            }
        } catch (error) {
            console.error("Ошибка загрузки файлов:", error);
            alert("Ошибка загрузки файлов.");
        } finally {
            setUploading(false);
        }
    };

    /**
     * Удаляет выбранный файл.
     *
     * @param {Object} fileToRemove - Файл для удаления.
     */
    const handleRemoveFile = (fileToRemove) => {
        setSelectedFiles(prevFiles => prevFiles.filter(file => file !== fileToRemove));
    };

    /**
     * Удаляет все выбранные файлы.
     */
    const handleRemoveAllFiles = () => {
        setSelectedFiles([]);
    };

    // Фильтруем файлы по типу
    const imageFiles = selectedFiles.filter(file => file.url);
    const pdfFiles = selectedFiles.filter(file => file.file.type === 'application/pdf');

    return (
        <div className="uploader-container">
            <h2>Перетащите файлы для загрузки</h2>
            <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? "active" : ""}`}
            >
                <input {...getInputProps()} />
                {isDragActive ? (
                    <p>Отпустите файлы для загрузки</p>
                ) : (
                    <p>Перетащите сюда файлы или нажмите, чтобы выбрать их</p>
                )}
            </div>
            {selectedFiles.length > 0 && (
                <div>
                    {pdfFiles.length > 0 && (
                        <div>
                            <h3>Загруженные PDF файлы:</h3>
                            <div className="file-list">
                                {pdfFiles.map((file, index) => (
                                    <div key={index} className="file-item">
                                        <p>{file.name}</p>
                                        <button className="remove-button" onClick={() => handleRemoveFile(file)}>X</button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {imageFiles.length > 0 && (
                        <div>
                            <h3>Предпросмотр изображений:</h3>
                            <Preview files={imageFiles} onRemove={handleRemoveFile} showRemoveButton={true} />
                        </div>
                    )}
                </div>
            )}
            <button
                onClick={handleRemoveAllFiles}
                className="page-button"
                disabled={uploading || selectedFiles.length === 0}
                style={{
                    backgroundColor: !uploading && selectedFiles.length > 0 ? 'red' : undefined,
                }}
            >
                Удалить все файлы
            </button>
            <button
                onClick={handleFileUpload}
                disabled={uploading || selectedFiles.length === 0}
                className="page-button"
            >
                Обработать
            </button>
        </div>
    );
};

export default FileUploader;
