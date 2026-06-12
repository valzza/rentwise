import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../../api/authApi";
import api from "../../api/axios";
import { useAuthStore } from "../../store/authStore";
import AuthLayout from "../../layouts/AuthLayout";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import toast from "react-hot-toast";

const DEMO_ACCOUNTS = [
  { label: "Admin", email: "admin@rentwise.com" },
  { label: "Landlord", email: "landlord@rentwise.com" },
  { label: "Tenant", email: "tenant@rentwise.com" },
];

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const doLogin = async (credentials) => {
    setLoading(true);
    try {
      const { data: tokens } = await authApi.login(credentials);
      const { data: user } = await api.get("/users/me", {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      login(user, tokens.access_token, tokens.refresh_token);
      toast.success("Welcome back!");
      navigate("/dashboard");
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    doLogin(form);
  };

  return (
    <AuthLayout title="Sign in to RentWise" subtitle="Welcome back — find your perfect rental">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <Input
          label="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <div className="flex justify-end">
          <Link to="/forgot-password" className="text-xs text-brand-600 hover:underline">
            Forgot password?
          </Link>
        </div>
        <Button type="submit" loading={loading} className="w-full">
          Sign in
        </Button>
      </form>

      {/* Demo account credentials */}
      <div className="mt-6 rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          Demo accounts
        </p>
        <ul className="space-y-1 text-gray-600">
          {DEMO_ACCOUNTS.map((acc) => (
            <li key={acc.email}>
              <span className="font-medium text-gray-900">{acc.label}:</span>{" "}
              <span className="font-mono text-xs">{acc.email}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-gray-600">
          Password (all): <span className="font-mono text-xs">Demo1234</span>
        </p>
      </div>

      <p className="mt-4 text-center text-sm text-gray-500">
        Don't have an account?{" "}
        <Link to="/register" className="text-brand-600 font-medium hover:underline">Register</Link>
      </p>
    </AuthLayout>
  );
}
