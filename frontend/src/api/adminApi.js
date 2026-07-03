import api from "./axios";

export const adminApi = {
  listUsers: (params) => api.get("/admin/users", { params }),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  listProperties: (params) => api.get("/admin/properties", { params }),
  reports: (params) => api.get("/admin/reports", { params }),
  auditLogs: (params) => api.get("/admin/audit-logs", { params }),
  listSettings: () => api.get("/admin/settings"),
  updateSetting: (key, value) => api.put(`/admin/settings/${key}`, { value }),

  // Export returns a file blob; trigger a browser download.
  exportEntity: async (entity, format = "csv") => {
    const res = await api.get(`/admin/export/${entity}`, {
      params: { format },
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement("a");
    a.href = url;
    const ext = format === "excel" ? "xlsx" : format;
    a.download = `${entity}.${ext}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  importEntity: (entity, file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post(`/admin/import/${entity}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};