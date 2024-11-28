import React from "react";
import DownloadButton from "../components/DownloadButton";
import Preview from "../components/Preview";
import { useNavigate } from "react-router-dom";
import { cleanUp } from "../api/api";

/**
 * Компонент страницы результатов.
 *
 * @param {Array} images - Массив имен обработанных изображений.
 * @returns {JSX.Element} - Компонент страницы результатов.
 */
const ResultsPage = ({ images }) => {
    // Хук для навигации
    const navigate = useNavigate();

    /**
     * Обрабатывает навигацию на главную страницу и очистку директорий.
     */
    const handleNavigateToHome = async () => {
        try {
            // Очистка директорий
            await cleanUp();
            // Переход на главную страницу
            navigate("/");
        } catch (error) {
            console.error("Ошибка очистки директорий:", error);
            alert("Не удалось очистить директории.");
        }
    };

    return (
        <div>
            <h2>Обработанные изображения</h2>
            {/* Компонент предпросмотра изображений */}
            <Preview
                files={images.map(image => ({
                    url: `http://127.0.0.1:8000/results/${image}`,
                    name: image
                }))}
                showRemoveButton={false}
            />
            {/* Компонент кнопок для скачивания файлов */}
            <DownloadButton />
            {/* Кнопка для перехода на главную страницу */}
            <button onClick={handleNavigateToHome} className="page-button">На главную</button>
        </div>
    );
};

export default ResultsPage;
