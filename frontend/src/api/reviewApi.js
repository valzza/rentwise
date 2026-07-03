import api from "./axios";

export const reviewApi = {
  create: (data) => api.post("/reviews", data),
  listForProperty: (propertyId) => api.get(`/reviews/property/${propertyId}`),
};