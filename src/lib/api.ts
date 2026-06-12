import axios from "axios";

/**
 * Production-ready API client configured with Axios.
 * Points to the FastAPI backend (proxied or direct).
 */
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
console.log("BASE_URL", BASE_URL);

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000, // 10s timeout to fail fast
});

// Request interceptor to attach tokens if auth is added later
api.interceptors.request.use((config) => {
  // const token = localStorage.getItem("access_token");
  // if (token) {
  //   config.headers.Authorization = `Bearer ${token}`;
  // }
  return config;
});

// Global response error handler
api.interceptors.response.use(
  (response) => {
    console.log("Status", response.status);
    console.log("Body", response.data);
    console.log("Array?", Array.isArray(response.data));
    return response;
  },
  (error) => {
    return Promise.reject(error);
  },
);
