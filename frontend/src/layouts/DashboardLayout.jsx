import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import NotificationBell from "../components/NotificationBell";
import Logo from "../components/Logo";
import { authApi } from "../api/authApi";
import { useAuthStore } from "../store/authStore";

const tenantNav = [
  { to: "/dashboard/tenant", label: "Overview" },
];
const landlordNav = [
  { to: "/dashboard/landlord", label: "Overview" },
  { to: "/properties", label: "Browse Properties" },
];
const adminNav = [
  { to: "/dashboard/admin", label: "Overview" },
];

export default function DashboardLayout({ children }) {
  const { user, isAdmin, isLandlord } = useAuth();
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const refreshToken = useAuthStore((s) => s.refreshToken);

  const nav = isAdmin ? adminNav : isLandlord ? landlordNav : tenantNav;

  const handleLogout = async () => {
    try { await authApi.logout(refreshToken); } catch { }
    logout();
    navigate("/login");
  };

  return (
    <div className="flex min-h-screen bg-[#f4f5f7]">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-5 py-4 border-b border-gray-200">
          <NavLink to="/"><Logo size="sm" /></NavLink>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1">
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive
                  ? "bg-brand-50 text-brand-700 ring-1 ring-brand-100"
                  : "text-gray-600 hover:bg-gray-100"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
          <NavLink to="/properties" className="flex items-center rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100">
            Properties
          </NavLink>
          <NavLink
            to="/dashboard/profile"
            className={({ isActive }) =>
              `flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive ? "bg-brand-50 text-brand-700 ring-1 ring-brand-100" : "text-gray-600 hover:bg-gray-100"
              }`
            }
          >
            My Profile
          </NavLink>
        </nav>
        <div className="border-t p-4">
          <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          <button
            onClick={handleLogout}
            className="mt-2 w-full rounded-lg px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b bg-white px-6">
          <h1 className="text-lg font-semibold text-gray-900">
            {user?.first_name} {user?.last_name}
          </h1>
          <NotificationBell />
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}