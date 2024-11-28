import React, { useState } from "react";
import ImageModal from "./ImageModal";

/**
 * Компонент для предпросмотра изображений.
 *
 * @param {Array} files - Массив файлов для предпросмотра.
 * @param {Function} onRemove - Функция обратного вызова для удаления файла.
 * @param {boolean} showRemoveButton - Флаг для отображения кнопки удаления.
 * @returns {JSX.Element} - Компонент для предпросмотра изображений.
 */
const Preview = ({ files, onRemove, showRemoveButton = false }) => {
    // Состояние для отслеживания текущего индекса изображения
    const [currentIndex, setCurrentIndex] = useState(null);

    /**
     * Открывает модальное окно с изображением по указанному индексу.
     *
     * @param {number} index - Индекс изображения для открытия.
     */
    const openModal = (index) => {
        setCurrentIndex(index);
    };

    /**
     * Закрывает модальное окно.
     */
    const closeModal = () => {
        setCurrentIndex(null);
    };

    /**
     * Переходит к следующему изображению.
     */
    const nextImage = () => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % files.length);
    };

    /**
     * Переходит к предыдущему изображению.
     */
    const prevImage = () => {
        setCurrentIndex((prevIndex) => (prevIndex - 1 + files.length) % files.length);
    };

    /**
     * Обрабатывает удаление файла.
     *
     * @param {Object} fileToRemove - Файл для удаления.
     */
    const handleRemove = (fileToRemove) => {
        if (onRemove) {
            onRemove(fileToRemove);
        }
    };

    return (
        <div>
            {/* Сетка предпросмотра изображений */}
            <div className="preview-grid">
                {files.map((file, index) => (
                    <div key={index} className="preview-item" onClick={() => openModal(index)}>
                        {/* Кнопка удаления файла */}
                        {showRemoveButton && (
                            <button
                                className="remove-button"
                                style={{ position: 'absolute', zIndex: '10', bottom: '0px', right: '0px' }}
                                onClick={(e) => { e.stopPropagation(); handleRemove(file); }}
                            >
                                X
                            </button>
                        )}
                        {/* Отображение изображения */}
                        <img src={file.url} alt={`Processed ${index}`} className="preview-image" />
                    </div>
                ))}
            </div>
            {/* Модальное окно для отображения изображения */}
            {currentIndex !== null && (
                <ImageModal
                    imageUrl={files[currentIndex].url}
                    onClose={closeModal}
                    onNext={nextImage}
                    onPrev={prevImage}
                />
            )}
        </div>
    );
};

export default Preview;
