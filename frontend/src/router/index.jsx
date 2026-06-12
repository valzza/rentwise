import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Spinner from "../components/ui/Spinner";

// Route-level lazy imports — each becomes its own chunk
const Landing           = lazy(() => import("../pages/Landing"));
const PropertyListing   = lazy(() => import("../pages/PropertyListing"));
const PropertyDetail    = lazy(() => import("../pages/PropertyDetail"));
const Login             = lazy(() => import("../pages/auth/Login"));
const Register          = lazy(() => import("../pages/auth/Register"));
const ForgotPassword    = lazy(() => import("../pages/auth/ForgotPassword"));
const TenantDashboard   = lazy(() => import("../pages/dashboard/TenantDashboard"));
const LandlordDashboard = lazy(() => import("../pages/dashboard/LandlordDashboard"));
const AdminDashboard    = lazy(() => import("../pages/dashboard/AdminDashboard"));
const NotFound          = lazy(() => import("../pages/NotFound"));

function ProtectedRoute({ children, requiredRole }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (requiredRole && !user?.roles?.includes(requiredRole)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="flex h-screen items-center justify-center"><Spinner size="lg" /></div>}>
        <Routes>
          {/* Public */}
          <Route path="/"             element={<Landing />} />
          <Route path="/properties"   element={<PropertyListing />} />
          <Route path="/properties/:id" element={<PropertyDetail />} />
          <Route path="/login"        element={<Login />} />
          <Route path="/register"     element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* Tenant */}
          <Route path="/dashboard/tenant" element={
            <ProtectedRoute requiredRole="tenant">
              <TenantDashboard />
            </ProtectedRoute>
          } />

          {/* Landlord */}
          <Route path="/dashboard/landlord" element={
            <ProtectedRoute requiredRole="landlord">
              <LandlordDashboard />
            </ProtectedRoute>
          } />

          {/* Admin */}
          <Route path="/dashboard/admin" element={
            <ProtectedRoute requiredRole="admin">
              <AdminDashboard />
            </ProtectedRoute>
          } />

          {/* Redirect /dashboard → role-specific dashboard */}
          <Route path="/dashboard" element={<DashboardRedirect />} />

          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

function DashboardRedirect() {
  const { user } = useAuth();
  if (user?.roles?.includes("admin")) return <Navigate to="/dashboard/admin" replace />;
  if (user?.roles?.includes("landlord")) return <Navigate to="/dashboard/landlord" replace />;
  return <Navigate to="/dashboard/tenant" replace />;
}
