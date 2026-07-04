import api from "./axios";

export const chatApi = {
  getPartners: (propertyId) => api.get(`/chat/property/${propertyId}/partners`),
};
