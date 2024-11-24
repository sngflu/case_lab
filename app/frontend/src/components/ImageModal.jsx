import React from "react";

const ImageModal = ({ imageUrl, onClose, onNext, onPrev }) => {
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <button className="modal-nav-button modal-prev-button" onClick={onPrev}>&lt;</button>
                <img src={imageUrl} alt="Fullscreen" className="modal-image" />
                <button className="modal-nav-button modal-next-button" onClick={onNext}>&gt;</button>
                <button className="modal-close-button" onClick={onClose}>X</button>
            </div>
        </div>
    );
};

export default ImageModal;
