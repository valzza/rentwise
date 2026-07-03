import api from "./axios";

export const authApi = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  refresh: (refreshToken) => api.post("/auth/refresh", { refresh_token: refreshToken }),
  logout: (refreshToken) => api.post("/auth/logout", { refresh_token: refreshToken }),
  getMe: () => api.get("/users/me"),
  updateMe: (data) => api.put("/users/me", data),
};