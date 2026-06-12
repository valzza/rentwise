import { useState } from "react";
import { useNotificationStore } from "../store/notificationStore";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const notifications = useNotificationStore((s) => s.notifications);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const markRead = useNotificationStore((s) => s.markRead);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative rounded-full p-2 text-gray-600 hover:bg-gray-100"
      >
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 z-50 w-80 rounded-xl border border-gray-200 bg-white shadow-lg">
          <div className="border-b px-4 py-3">
            <p className="font-semibold text-gray-900">Notifications</p>
          </div>
          <ul className="max-h-80 overflow-y-auto divide-y">
            {notifications.length === 0 && (
              <li className="px-4 py-6 text-center text-sm text-gray-500">No notifications</li>
            )}
            {notifications.map((n) => (
              <li
                key={n.id}
                onClick={() => markRead(n.id)}
                className={`cursor-pointer px-4 py-3 hover:bg-gray-50 ${!n.is_read ? "bg-brand-50" : ""}`}
              >
                <p className="text-sm font-medium text-gray-900">{n.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
