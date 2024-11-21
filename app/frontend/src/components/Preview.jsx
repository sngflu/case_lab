import React from "react";

const Preview = ({ files }) => {
    return (
        <div>
            <h3>Предпросмотр обработанных изображений</h3>
            <div className="preview-grid">
                {files.map((file, index) => (
                    <div key={index} className="preview-item">
                        <img src={file.url} alt={`Processed ${index}`} />
                        <p>{file.name}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Preview;
