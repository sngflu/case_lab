import React from 'react';
import { Route, Routes } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';

/**
 * Главный компонент приложения.
 *
 * @returns {JSX.Element} - Главный компонент приложения.
 */
const App = () => {
  // Состояние для хранения обработанных изображений
  const [images, setImages] = React.useState([]);

  /**
   * Обрабатывает завершение обработки изображений.
   *
   * @param {Array} processedImages - Массив обработанных изображений.
   */
  const handleProcessingComplete = (processedImages) => {
    setImages(processedImages);
  };

  return (
    <div className="container">
      {/* Маршруты приложения */}
      <Routes>
        {/* Маршрут для страницы загрузки файлов */}
        <Route path="/" element={<UploadPage onProcessingComplete={handleProcessingComplete} />} />
        {/* Маршрут для страницы результатов */}
        <Route path="/results" element={<ResultsPage images={images} onDownload={() => { }} />} />
      </Routes>
    </div>
  );
};

export default App;
