import { lazy, Suspense, useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import api from "../../api/axios";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import toast from "react-hot-toast";

// Lazy — recharts only loads when Reports tab is viewed
const ReportsChart = lazy(() => import("../../components/EarningsChart"));

const TABS = ["Users", "Properties", "Reports", "Settings"];

export default function AdminDashboard() {
  const [tab, setTab] = useState("Users");
  const [users, setUsers] = useState([]);
  const [properties, setProperties] = useState([]);
  const [reports, setReports] = useState(null);
  const [settings, setSettings] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (tab === "Users") {
      setLoading(true);
      api.get("/admin/users", { params: { search, page: 1, page_size: 30 } })
        .then(({ data }) => setUsers(data.items ?? [])).finally(() => setLoading(false));
    }
    if (tab === "Properties") {
      setLoading(true);
      api.get("/admin/properties", { params: { page: 1, page_size: 30 } })
        .then(({ data }) => setProperties(data.items ?? [])).finally(() => setLoading(false));
    }
    if (tab === "Reports") {
      setLoading(true);
      api.get("/admin/reports").then(({ data }) => setReports(data)).finally(() => setLoading(false));
    }
    if (tab === "Settings") {
      setLoading(true);
      api.get("/admin/settings").then(({ data }) => setSettings(data)).finally(() => setLoading(false));
    }
  }, [tab, search]);

  const toggleActive = async (user) => {
    await api.put(`/admin/users/${user.id}`, { is_active: !user.is_active });
    setUsers((us) => us.map((u) => u.id === user.id ? { ...u, is_active: !u.is_active } : u));
    toast.success("User updated");
  };

  return (
    <DashboardLayout>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">Admin Dashboard</h1>

      <div className="flex gap-1 border-b mb-6">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t ? "border-brand-500 text-brand-600" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {t}
          </button>
        ))}
      </div>

      {loading ? <div className="flex justify-center py-12"><Spinner size="lg" /></div> : (
        <>
          {tab === "Users" && (
            <div className="space-y-4">
              <Input placeholder="Search by name or email..." value={search} onChange={(e) => setSearch(e.target.value)} />
              <div className="overflow-x-auto rounded-xl border bg-white">
                <table className="w-full text-sm">
                  <thead className="border-b bg-gray-50 text-xs text-gray-500 uppercase">
                    <tr>
                      {["ID", "Name", "Email", "Active", "Actions"].map((h) => (
                        <th key={h} className="px-4 py-3 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {users.map((u) => (
                      <tr key={u.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-gray-500">{u.id}</td>
                        <td className="px-4 py-3 font-medium">{u.first_name} {u.last_name}</td>
                        <td className="px-4 py-3 text-gray-500">{u.email}</td>
                        <td className="px-4 py-3"><Badge color={u.is_active ? "green" : "red"}>{u.is_active ? "Active" : "Inactive"}</Badge></td>
                        <td className="px-4 py-3">
                          <Button size="sm" variant="secondary" onClick={() => toggleActive(u)}>
                            {u.is_active ? "Deactivate" : "Activate"}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "Properties" && (
            <div className="overflow-x-auto rounded-xl border bg-white">
              <table className="w-full text-sm">
                <thead className="border-b bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>{["ID", "Title", "Price", "Status"].map((h) => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y">
                  {properties.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-500">{p.id}</td>
                      <td className="px-4 py-3 font-medium">{p.title}</td>
                      <td className="px-4 py-3">${Number(p.price).toLocaleString()}</td>
                      <td className="px-4 py-3"><Badge color={p.status === "active" ? "green" : "gray"}>{p.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "Reports" && reports && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Total Users",      value: reports.total_users },
                { label: "Total Properties", value: reports.total_properties },
                { label: "Active Leases",    value: reports.active_leases },
                { label: "Total Revenue",    value: `$${Number(reports.total_revenue).toLocaleString()}` },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-xl border bg-white px-6 py-5">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
                </div>
              ))}
            </div>
          )}

          {tab === "Settings" && (
            <div className="space-y-3">
              {settings.map((s) => (
                <div key={s.key} className="flex items-center gap-4 rounded-xl border bg-white px-5 py-4">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{s.key}</p>
                    {s.description && <p className="text-xs text-gray-500">{s.description}</p>}
                  </div>
                  <span className="text-sm text-gray-700 bg-gray-100 rounded px-2 py-1">{s.value}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  );
}
