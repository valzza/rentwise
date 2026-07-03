import api from "./axios";

export const savedPropertiesApi = {
  list: () => api.get("/saved-properties"),
  toggle: (propertyId) => api.post(`/saved-properties/${propertyId}`),
  remove: (propertyId) => api.delete(`/saved-properties/${propertyId}`),
};