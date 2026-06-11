import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);
  const setUser = useAuthStore((s) => s.setUser);

  const isAuthenticated = !!accessToken;
  const isAdmin = user?.roles?.includes("admin") ?? false;
  const isLandlord = user?.roles?.includes("landlord") ?? false;
  const isTenant = user?.roles?.includes("tenant") ?? false;

  return { user, isAuthenticated, isAdmin, isLandlord, isTenant, login, logout, setUser };
}
