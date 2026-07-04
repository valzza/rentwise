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

    if (!socketInstance) {
      socketInstance = io("/", {
        auth: { token: accessToken },
        transports: ["websocket"],
      });
    } else if (!socketInstance.connected) {
      socketInstance.auth = { token: accessToken };
      socketInstance.connect();
    }

    socketInstance.on("notification", (payload) => {
      addNotification(payload);
    });

    socketInstance.on("chat_history", (payload) => {
      const room_id = Array.isArray(payload) ? payload[0]?.room_id : payload?.room_id;
      const messages = Array.isArray(payload) ? payload : payload?.messages ?? [];
      if (room_id) setHistory(room_id, messages);
    });

    socketInstance.on("new_message", (message) => {
      addMessage(message.room_id, message);
    });

    const onChatInbox = (payload) => {
      window.dispatchEvent(new CustomEvent("rentwise:chat-inbox", { detail: payload }));
    };
    socketInstance.on("chat_inbox", onChatInbox);

    return () => {
      socketInstance?.off("chat_inbox", onChatInbox);
      // Keep socket alive across page navigations — only disconnect on logout
    };
  }, [accessToken, user]);

  return socketInstance;
}

export function getSocket() {
  return socketInstance;
}