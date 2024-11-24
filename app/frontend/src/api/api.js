import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export const uploadFiles = async (formData, onUploadProgress) => {
    return axios.post(`${API_URL}/process/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress,
    });
};

export const downloadZip = async () => {
    return axios.get(`${API_URL}/download/pics`, {
        responseType: "blob",
    });
};

export const downloadJson = async () => {
    return axios.get(`${API_URL}/download/json/`, {
        responseType: "blob",
    });
};

export const cleanUp = async () => {
    return axios.post(`${API_URL}/cleanup/`);
};
