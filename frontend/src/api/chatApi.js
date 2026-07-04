import api from "./axios";

export const chatApi = {
  getPartners: (propertyId) => api.get(`/chat/property/${propertyId}/partners`),
  getMessages: (propertyId, otherUserId) =>
    api.get(`/chat/property/${propertyId}/messages`, { params: { other_user_id: otherUserId } }),
};