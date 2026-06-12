import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../../api/authApi";
import api from "../../api/axios";
import { useAuthStore } from "../../store/authStore";
import AuthLayout from "../../layouts/AuthLayout";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import toast from "react-hot-toast";

export default function Register() {
  const [form, setForm] = useState({
    first_name: "", last_name: "", email: "", password: "", role: "tenant",
  });
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data: tokens } = await authApi.register(form);
      // Pass the token directly — avoids race with Zustand persist rehydration
      const { data: user } = await api.get("/users/me", {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      login(user, tokens.access_token, tokens.refresh_token);
      toast.success(`Account created — welcome, ${user.first_name}!`);
      navigate("/dashboard");
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create your account" subtitle="Join RentWise today">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Input label="First name" value={form.first_name} onChange={set("first_name")} required />
          <Input label="Last name"  value={form.last_name}  onChange={set("last_name")}  required />
        </div>
        <Input label="Email" type="email" value={form.email} onChange={set("email")} required />
        <Input label="Password" type="password" value={form.password} onChange={set("password")} required />

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700">I am a</label>
          <div className="flex gap-3">
            {["tenant", "landlord"].map((r) => (
              <label key={r} className={`flex flex-1 cursor-pointer items-center justify-center rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${form.role === r ? "border-brand-400 bg-brand-50 text-brand-700" : "border-gray-300 text-gray-600 hover:border-gray-400"}`}>
                <input type="radio" name="role" value={r} checked={form.role === r} onChange={set("role")} className="sr-only" />
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </label>
            ))}
          </div>
        </div>

        <Button type="submit" loading={loading} className="w-full">
          Create account
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-gray-500">
        Already have an account?{" "}
        <Link to="/login" className="text-brand-600 font-medium hover:underline">Sign in</Link>
      </p>
    </AuthLayout>
  );
}
