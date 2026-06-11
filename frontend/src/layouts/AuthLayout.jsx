import { Link } from "react-router-dom";
import Logo from "../components/Logo";

export default function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f4f5f7] px-4">
      {/* subtle teal top accent line */}
      <div className="fixed inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-400 via-brand-500 to-brand-600" />
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center text-center">
          <Link to="/"><Logo size="lg" /></Link>
          {title && <h1 className="mt-6 text-2xl font-semibold text-gray-900">{title}</h1>}
          {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-card">
          {children}
        </div>
      </div>
    </div>
  );
}
