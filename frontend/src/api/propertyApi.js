import api from "./axios";

export const propertyApi = {
  search: (params) => api.get("/properties/search", { params }),
  getFeatured: () => api.get("/properties/featured"),
  getById: (id) => api.get(`/properties/${id}`),
  create: (data) => api.post("/properties", data),
  update: (id, data) => api.put(`/properties/${id}`, data),
  remove: (id) => api.delete(`/properties/${id}`),
  getCities: () => api.get("/properties/cities"),
  getNeighborhoods: (cityId) => api.get("/properties/neighborhoods", { params: { city_id: cityId } }),
  getAmenities: () => api.get("/properties/amenities"),
  saveToggle: (propertyId) => api.post(`/saved-properties/${propertyId}`),
  generateDescription: (bulletPoints) =>
    api.post("/properties/generate-description", { bullet_points: bulletPoints }),
};
