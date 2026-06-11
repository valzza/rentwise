import api from "./axios";

export const applicationApi = {
  create: (data) => api.post("/applications", data),
  listMine: (params) => api.get("/applications", { params }),
  listForProperty: (propertyId, params) => api.get(`/applications/property/${propertyId}`, { params }),
  updateStatus: (id, status) => api.put(`/applications/${id}/status`, { status }),
};
