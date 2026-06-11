import { useEffect, useRef } from "react";
import { io } from "socket.io-client";
import { useAuthStore } from "../store/authStore";
import { useNotificationStore } from "../store/notificationStore";
import { useChatStore } from "../store/chatStore";

let socketInstance = null;

export function useSocket() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const addNotification = useNotificationStore((s) => s.addNotification);
  const addMessage = useChatStore((s) => s.addMessage);
  const setHistory = useChatStore((s) => s.setHistory);

  useEffect(() => {
    if (!accessToken || !user) {
      if (socketInstance) {
        socketInstance.disconnect();
        socketInstance = null;
      }
      return;
    }

    if (socketInstance?.connected) return;

    socketInstance = io("/", {
      auth: { token: accessToken },
      transports: ["websocket"],
    });

    socketInstance.on("notification", (payload) => {
      addNotification(payload);
    });

    socketInstance.on("chat_history", (messages) => {
      // The room key comes from the messages themselves
      if (messages.length > 0) {
        const { room_id } = messages[0];
        setHistory(room_id, messages);
      }
    });

    socketInstance.on("new_message", (message) => {
      addMessage(message.room_id, message);
    });

    return () => {
      // Keep socket alive across page navigations — only disconnect on logout
    };
  }, [accessToken, user]);

  return socketInstance;
}

export function getSocket() {
  return socketInstance;
}
