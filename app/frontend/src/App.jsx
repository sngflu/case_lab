import React from 'react';
import { Route, Routes } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';

const App = () => {
  const [images, setImages] = React.useState([]);

  const handleProcessingComplete = (processedImages) => {
    setImages(processedImages);
  };

  return (
    <div className="container">
      <Routes>
        <Route path="/" element={<UploadPage onProcessingComplete={handleProcessingComplete} />} />
        <Route path="/results" element={<ResultsPage images={images} onDownload={() => { }} />} />
      </Routes>
    </div>
  );
};

export default App;
