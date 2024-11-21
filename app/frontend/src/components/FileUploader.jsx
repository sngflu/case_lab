import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadFiles } from "../api/api";

const FileUploader = ({ onUpload }) => {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [uploading, setUploading] = useState(false);

    const onDrop = useCallback((acceptedFiles) => {
        const filesWithPreviews = acceptedFiles.map(file => ({
            file,
            preview: URL.createObjectURL(file), // Для временного предпросмотра
            name: file.name,
        }));
        setSelectedFiles(filesWithPreviews);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: "image/png",
        multiple: true,
    });

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
                <div className="preview-grid">
                    {selectedFiles.map((file, index) => (
                        <div key={index} className="preview-item">
                            <img src={file.preview} alt={file.name} className="preview-image" />
                            <p>{file.name}</p>
                        </div>
                    ))}
                </div>
            )}
            <button onClick={handleFileUpload} disabled={uploading || selectedFiles.length === 0}>
                {uploading ? "Загрузка..." : "Обработать"}
            </button>
        </div>
    );
};

export default FileUploader;
