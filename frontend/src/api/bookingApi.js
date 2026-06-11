import api from "./axios";

export const bookingApi = {
  create: (data) => api.post("/bookings", data),
  list: (params) => api.get("/bookings", { params }),
  updateStatus: (id, status) => api.put(`/bookings/${id}/status`, { status }),
};
