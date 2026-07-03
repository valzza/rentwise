import api from "./axios";

export const leaseApi = {
  create: (data) => api.post("/leases", data),
  list: () => api.get("/leases"),
  getById: (id) => api.get(`/leases/${id}`),
};