import api from "./axios";

export const paymentApi = {
  createIntent: (leaseId) => api.post("/payments/create-intent", { lease_id: leaseId }),
  listMine: (params) => api.get("/payments/my", { params }),
  getEarnings: () => api.get("/payments/earnings"),
};
