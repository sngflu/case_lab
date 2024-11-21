import React from "react";
import DownloadButton from "../components/DownloadButton";
import { useNavigate } from "react-router-dom";
import { cleanUp } from "../api/api";

const ResultsPage = ({ images }) => {
    const navigate = useNavigate();

    const handleNavigateToHome = async () => {
        try {
            await cleanUp();
            navigate("/");
        } catch (error) {
            console.error("Ошибка при очистке директорий:", error);
            alert("Не удалось очистить директории.");
        }
    };

    return (
        <div>
            <h2>Обработанные изображения</h2>
            {images.length > 0 ? (
                <div className="preview-grid">
                    {images.map((image, index) => (
                        <div key={index} className="preview-item">
                            <img src={`http://127.0.0.1:8000/results/${image}`} alt={image} className="preview-image" />
                            <p>{image}</p>
                        </div>
                    ))}
                </div>
            ) : (
                <p>Нет обработанных изображений</p>
            )}
            <DownloadButton />
            <button onClick={handleNavigateToHome}>На главную</button>
        </div>
    );
};

export default ResultsPage;
