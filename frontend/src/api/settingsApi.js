import api from "./axios";

export const settingsApi = {
  getPublic: () => api.get("/settings/public"),
};