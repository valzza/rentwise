import AppRouter from "./router";
import { useSocket } from "./hooks/useSocket";
import { useEffect } from "react";
import { useAuth } from "./hooks/useAuth";
import { useNotificationStore } from "./store/notificationStore";

export default function App() {
  // Initialize Socket.IO connection for authenticated users
  useSocket();

  const { isAuthenticated } = useAuth();
  const fetchNotifications = useNotificationStore((s) => s.fetchNotifications);

  // Load notifications on first auth
  useEffect(() => {
    if (isAuthenticated) fetchNotifications();
  }, [isAuthenticated]);

  return <AppRouter />;
}
