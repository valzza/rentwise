import { create } from "zustand";

/** Stable empty list — avoids infinite re-renders in Zustand selectors. */
export const EMPTY_MESSAGES = [];

/** Must match backend chat_handlers._room_id format. */
export function chatRoomId(propertyId, userA, userB) {
  const lo = Math.min(userA, userB);
  const hi = Math.max(userA, userB);
  return `chat:${propertyId}:${lo}_${hi}`;
}

export const useChatStore = create((set) => ({
  // rooms keyed by chatRoomId(...) e.g. chat:7:3_5
  rooms: {},

  setHistory: (roomKey, messages) =>
    set((state) => ({
      rooms: { ...state.rooms, [roomKey]: messages },
    })),

  addMessage: (roomKey, message) =>
    set((state) => ({
      rooms: {
        ...state.rooms,
        [roomKey]: [...(state.rooms[roomKey] || EMPTY_MESSAGES), message],
      },
    })),
}));
