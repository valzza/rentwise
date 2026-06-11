import { create } from "zustand";
import api from "../api/axios";

export const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,

  fetchNotifications: async () => {
    try {
      const { data } = await api.get("/notifications");
      const unread = data.filter((n) => !n.is_read).length;
      set({ notifications: data, unreadCount: unread });
    } catch {
      // silently fail — user may not be logged in yet
    }
  },

  addNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    })),

  markRead: async (id) => {
    await api.post(`/notifications/${id}/read`);
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    }));
  },

  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));
