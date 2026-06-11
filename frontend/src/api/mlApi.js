import api from "./axios";

export const mlApi = {
  estimatePrice: (features) => api.post("/ml/estimate-price", features),
};
