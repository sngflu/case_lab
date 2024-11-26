import axios from "axios";

// URL для API
const API_URL = "http://127.0.0.1:8000";

/**
 * Загружает файлы на сервер.
 *
 * @param {FormData} formData - Данные формы для загрузки.
 * @returns {Promise} - Промис, который разрешается ответом от сервера.
 */
export const uploadFiles = async (formData) => {
    return axios.post(`${API_URL}/process/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
    });
};

/**
 * Скачивает ZIP-архив с обработанными изображениями.
 *
 * @returns {Promise} - Промис, который разрешается ответом от сервера с типом "blob".
 */
export const downloadZip = async () => {
    return axios.get(`${API_URL}/download/pics`, {
        responseType: "blob",
    });
};

/**
 * Скачивает JSON-файлы с аннотациями.
 *
 * @returns {Promise} - Промис, который разрешается ответом от сервера с типом "blob".
 */
export const downloadJson = async () => {
    return axios.get(`${API_URL}/download/json/`, {
        responseType: "blob",
    });
};

/**
 * Очищает временные файлы на сервере.
 *
 * @returns {Promise} - Промис, который разрешается ответом от сервера.
 */
export const cleanUp = async () => {
    return axios.post(`${API_URL}/cleanup/`);
};
