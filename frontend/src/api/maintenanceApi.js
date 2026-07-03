import api from "./axios";

export const maintenanceApi = {
  create: (data) => api.post("/maintenance", data),
  listMine: () => api.get("/maintenance"),
  listLandlord: (params) => api.get("/maintenance/landlord", { params }),
  updateStatus: (id, data) => api.put(`/maintenance/${id}`, data),
};