import React, { useState } from "react";
import FileUploader from "../components/FileUploader";
import { useNavigate } from 'react-router-dom';

const UploadPage = ({ onProcessingComplete }) => {
    const [processedFiles, setProcessedFiles] = useState([]);
    const navigate = useNavigate();

    const handleUpload = (files) => {
        console.log("Uploading files:", files);
        setProcessedFiles(files);
        onProcessingComplete(files);
        navigate('/results');
    };

    return (
        <div>
            <FileUploader onUpload={handleUpload} />
            {processedFiles.length > 0 && <Preview files={processedFiles} />}
        </div>
    );
};

export default UploadPage;
