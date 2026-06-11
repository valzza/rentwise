import axios from "axios";
import { useAuthStore } from "../store/authStore";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  // Serialize array params as repeated keys (amenity_ids=1&amenity_ids=2)
  // which is what FastAPI's List[int] query params expect — not the default
  // bracketed form (amenity_ids[]=1).
  paramsSerializer: { indexes: null },
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401: attempt token refresh, then retry the original request once
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    const url = originalRequest?.url || "";
    // Never attempt a token refresh on the auth endpoints themselves — a failed
    // login/refresh/register must surface its own error (e.g. "Invalid email or
    // password") instead of triggering a refresh.
    const isAuthEndpoint = /\/auth\/(login|refresh|register)/.test(url);

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      // No session to refresh -> just fail (avoids a spurious 422 on /auth/refresh).
      if (!useAuthStore.getState().refreshToken) {
        useAuthStore.getState().logout();
        return Promise.reject(error);
      }
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        const { data } = await axios.post("/api/auth/refresh", {
          refresh_token: refreshToken,
        });

        useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
        processQueue(null, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
