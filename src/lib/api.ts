import axios from "axios";

/**
 * Production-ready API client configured with Axios.
 * Points to the FastAPI backend (proxied or direct).
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60s timeout for heavy LLM routes
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
  (response) => response,
  (error) => {
    // We could integrate a global toast notification here
    // e.g., toast.error(error.response?.data?.detail || "An unexpected error occurred");
    return Promise.reject(error);
  }
);
