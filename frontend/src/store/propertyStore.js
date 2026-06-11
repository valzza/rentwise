import { create } from "zustand";
import { propertyApi } from "../api/propertyApi";

export const usePropertyStore = create((set) => ({
  properties: [],
  total: 0,
  page: 1,
  pages: 1,
  loading: false,
  filters: {},

  setFilters: (filters) => set({ filters, page: 1 }),
  setPage: (page) => set({ page }),

  search: async (params) => {
    set({ loading: true });
    try {
      const { data } = await propertyApi.search(params);
      set({
        properties: data.items,
        total: data.total,
        page: data.page,
        pages: data.pages,
      });
    } finally {
      set({ loading: false });
    }
  },
}));
