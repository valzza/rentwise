// Lazy-loaded — only imports socket.io-client when chat is opened
import { useState, useEffect, useRef } from "react";
import { getSocket } from "../hooks/useSocket";
import { useChatStore, chatRoomId, EMPTY_MESSAGES } from "../store/chatStore";
import { chatApi } from "../api/chatApi";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";

export default function ChatDrawer({ property, otherUserId, onClose }) {
  const { user } = useAuth();
  const setHistory = useChatStore((s) => s.setHistory);
  const [text, setText] = useState("");
  const bottomRef = useRef(null);
  const roomKey = user ? chatRoomId(property.id, user.id, otherUserId) : null;
  const messages = useChatStore((s) =>
    roomKey ? s.rooms[roomKey] ?? EMPTY_MESSAGES : EMPTY_MESSAGES
  );

  useEffect(() => {
    if (!roomKey || !property?.id || !otherUserId) return;

    chatApi.getMessages(property.id, otherUserId)
      .then(({ data }) => setHistory(data.room_id ?? roomKey, data.messages ?? []))
      .catch(() => toast.error("Could not load chat history from database"));
  }, [property.id, otherUserId, roomKey, setHistory]);

  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const onHistory = (payload) => {
      const room_id = Array.isArray(payload) ? payload[0]?.room_id : payload?.room_id;
      const messages = Array.isArray(payload) ? payload : payload?.messages ?? [];
      if (room_id) setHistory(room_id, messages);
    };

    const join = () => {
      socket.emit("join_chat", { property_id: property.id, other_user_id: otherUserId });
    };

    socket.on("chat_history", onHistory);
    if (socket.connected) join();
    else socket.on("connect", join);

    const onError = (payload) => {
      toast.error(payload?.detail ?? "Message not saved to database");
    };
    socket.on("chat_error", onError);

    return () => {
      socket.off("chat_history", onHistory);
      socket.off("connect", join);
      socket.off("chat_error", onError);
    };
  }, [property.id, otherUserId, setHistory]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const socket = getSocket();
    socket?.emit("send_message", { property_id: property.id, other_user_id: otherUserId, message: trimmed });
    setText("");
  };

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-white border-l border-gray-200 shadow-xl flex flex-col z-40">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="font-semibold text-gray-900 text-sm">Chat — {property.title}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-center text-xs text-gray-400 mt-6">No messages yet. Start the conversation!</p>
        )}
        {messages.map((m, i) => {
          const mine = Number(m.sender_id) === Number(user?.id);
          return (
            <div key={i} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm ${mine ? "bg-brand-500 text-white" : "bg-gray-100 text-gray-900"}`}>
                {m.message}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <div className="border-t p-3 flex gap-2">
        <input
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          placeholder="Type a message..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          onClick={send}
          className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600"
        >
          Send
        </button>
      </div>
    </div>
  );
}