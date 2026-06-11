import { create } from "zustand";

export const useChatStore = create((set, get) => ({
  // rooms keyed by roomKey = `${propertyId}:${otherUserId}`
  rooms: {},

  setHistory: (roomKey, messages) =>
    set((state) => ({
      rooms: { ...state.rooms, [roomKey]: messages },
    })),

  addMessage: (roomKey, message) =>
    set((state) => ({
      rooms: {
        ...state.rooms,
        [roomKey]: [...(state.rooms[roomKey] || []), message],
      },
    })),

  getMessages: (roomKey) => get().rooms[roomKey] || [],
}));
