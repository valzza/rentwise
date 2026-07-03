import api from "./axios";

export const fileApi = {
  upload: (file, { entity = "misc", entityId = 0, linkProperty = false } = {}) => {
    const form = new FormData();
    form.append("file", file);
    form.append("entity", entity);
    form.append("entity_id", entityId);
    form.append("link_property", linkProperty);
    return api.post("/files/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};