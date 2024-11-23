import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadFiles } from "../api/api";
import Preview from "../components/Preview";

const FileUploader = ({ onUpload }) => {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [uploading, setUploading] = useState(false);

    const onDrop = useCallback((acceptedFiles) => {
        const filesWithPreviews = acceptedFiles.map(file => {
            const previewUrl = URL.createObjectURL(file);
            console.log(`File: ${file.name}, Preview URL: ${previewUrl}`);
            return {
                file,
                url: previewUrl,
                name: file.name,
            };
        });
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
                <div>
                    <h3>Выбранные файлы для загрузки:</h3>
                    <Preview files={selectedFiles} />
                </div>
            )}
            <button onClick={handleFileUpload} disabled={uploading || selectedFiles.length === 0} className="page-button">
                {uploading ? "Загрузка..." : "Обработать"}
            </button>
        </div>
    );
};

export default FileUploader;
