import React from "react";
import DownloadButton from "../components/DownloadButton";
import Preview from "../components/Preview";
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

    const handleDownload = () => {
        // TODO: add some logic
    };

    return (
        <div>
            <h2>Обработанные изображения</h2>
            <Preview files={images.map(image => ({
                url: `http://127.0.0.1:8000/results/${image}`,
                name: image
            }))} />
            <DownloadButton onDownload={handleDownload} />
            <button onClick={handleNavigateToHome} className="page-button">На главную</button>
        </div>
    );
};

export default ResultsPage;
