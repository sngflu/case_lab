import React from "react";

/**
 * Компонент модального окна для отображения изображения.
 *
 * @param {string} imageUrl - URL изображения для отображения.
 * @param {Function} onClose - Функция обратного вызова для закрытия модального окна.
 * @param {Function} onNext - Функция обратного вызова для перехода к следующему изображению.
 * @param {Function} onPrev - Функция обратного вызова для перехода к предыдущему изображению.
 * @returns {JSX.Element} - Компонент модального окна для отображения изображения.
 */
const ImageModal = ({ imageUrl, onClose, onNext, onPrev }) => {
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                {/* Кнопка для перехода к предыдущему изображению */}
                <button className="modal-nav-button modal-prev-button" onClick={onPrev}>&lt;</button>
                {/* Отображение изображения */}
                <img src={imageUrl} alt="Fullscreen" className="modal-image" />
                {/* Кнопка для перехода к следующему изображению */}
                <button className="modal-nav-button modal-next-button" onClick={onNext}>&gt;</button>
                {/* Кнопка для закрытия модального окна */}
                <button className="modal-close-button" onClick={onClose}>X</button>
            </div>
        </div>
    );
};

export default ImageModal;
