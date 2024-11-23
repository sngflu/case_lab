import React, { useState } from "react";
import ImageModal from "./ImageModal";

const Preview = ({ files }) => {
    const [currentIndex, setCurrentIndex] = useState(null);

    const openModal = (index) => {
        setCurrentIndex(index);
    };

    const closeModal = () => {
        setCurrentIndex(null);
    };

    const nextImage = () => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % files.length);
    };

    const prevImage = () => {
        setCurrentIndex((prevIndex) => (prevIndex - 1 + files.length) % files.length);
    };

    return (
        <div>
            <div className="preview-grid">
                {files.map((file, index) => (
                    <div key={index} className="preview-item" onClick={() => openModal(index)}>
                        <img src={file.url} alt={`Processed ${index}`} className="preview-image" />
                        <p>{file.name}</p>
                    </div>
                ))}
            </div>
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
