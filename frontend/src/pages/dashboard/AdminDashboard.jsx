import { lazy, Suspense, useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { adminApi } from "../../api/adminApi";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import toast from "react-hot-toast";

// Lazy — recharts only loads when Reports tab is viewed
const ReportsChart = lazy(() => import("../../components/EarningsChart"));

const TABS = ["Users", "Properties", "Reports", "Audit Logs", "CMS / Settings", "Import / Export"];
const EXPORTABLE = ["properties", "users", "bookings", "applications", "payments"];

export default function AdminDashboard() {
  const [tab, setTab] = useState("Users");
  const [users, setUsers] = useState([]);
  const [properties, setProperties] = useState([]);
  const [reports, setReports] = useState(null);
  const [reportRange, setReportRange] = useState({ date_from: "", date_to: "" });
  const [auditLogs, setAuditLogs] = useState([]);
  const [settings, setSettings] = useState([]);
  const [settingEdits, setSettingEdits] = useState({});
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  // Import state
  const [importEntity, setImportEntity] = useState("users");
  const [importFile, setImportFile] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    if (tab === "Users") {
      setLoading(true);
      adminApi.listUsers({ search, page: 1, page_size: 30 })
        .then(({ data }) => setUsers(data.items ?? [])).finally(() => setLoading(false));
    }
    if (tab === "Properties") {
      setLoading(true);
      adminApi.listProperties({ page: 1, page_size: 30 })
        .then(({ data }) => setProperties(data.items ?? [])).finally(() => setLoading(false));
    }
    if (tab === "Reports") {
      setLoading(true);
      adminApi.reports({ date_from: reportRange.date_from || undefined, date_to: reportRange.date_to || undefined })
        .then(({ data }) => setReports(data)).finally(() => setLoading(false));
    }
    if (tab === "Audit Logs") {
      setLoading(true);
      adminApi.auditLogs({ page: 1, page_size: 50 })
        .then(({ data }) => setAuditLogs(data.items ?? [])).finally(() => setLoading(false));
    }
    if (tab === "CMS / Settings") {
      setLoading(true);
      adminApi.listSettings().then(({ data }) => {
        setSettings(data);
        setSettingEdits(Object.fromEntries(data.map((s) => [s.key, s.value])));
      }).finally(() => setLoading(false));
    }
  }, [tab, search, reportRange]);

  const toggleActive = async (user) => {
    await adminApi.updateUser(user.id, { is_active: !user.is_active });
    setUsers((us) => us.map((u) => u.id === user.id ? { ...u, is_active: !u.is_active } : u));
    toast.success("User updated");
  };

  const saveSetting = async (key) => {
    try {
      await adminApi.updateSetting(key, settingEdits[key]);
      setSettings((ss) => ss.map((s) => s.key === key ? { ...s, value: settingEdits[key] } : s));
      toast.success("Saved");
    } catch { toast.error("Save failed"); }
  };

  const runImport = async (e) => {
    e.preventDefault();
    if (!importFile) return toast.error("Choose a file first");
    setImporting(true);
    try {
      const { data } = await adminApi.importEntity(importEntity, importFile);
      setImportResult(data);
      toast.success(`Imported ${data.inserted} row(s)`);
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Import failed");
    } finally {
      setImporting(false);
    }
  };

  return (
    <DashboardLayout>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">Admin Dashboard</h1>

      <div className="flex gap-1 border-b mb-6 flex-wrap">
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
                      {["ID", "Name", "Email", "Roles", "Active", "Actions"].map((h) => (
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
                        <td className="px-4 py-3 text-gray-500">{(u.roles ?? []).join(", ")}</td>
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
            <div className="space-y-6">
              <div className="flex flex-wrap items-end gap-3">
                <Input label="From" type="date" value={reportRange.date_from} onChange={(e) => setReportRange((r) => ({ ...r, date_from: e.target.value }))} />
                <Input label="To" type="date" value={reportRange.date_to} onChange={(e) => setReportRange((r) => ({ ...r, date_to: e.target.value }))} />
                <Button variant="secondary" onClick={() => setReportRange({ date_from: "", date_to: "" })}>Clear</Button>
              </div>
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
              {reports.monthly?.length > 0 && (
                <div className="rounded-xl border bg-white p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Monthly Revenue</h3>
                  <Suspense fallback={<Spinner />}>
                    <ReportsChart data={reports.monthly} />
                  </Suspense>
                </div>
              )}
            </div>
          )}

          {tab === "Audit Logs" && (
            <div className="overflow-x-auto rounded-xl border bg-white">
              <table className="w-full text-sm">
                <thead className="border-b bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>{["Time", "User", "Action", "Entity", "Entity ID", "IP"].map((h) => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y">
                  {auditLogs.length === 0 && (
                    <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-500">No audit entries yet.</td></tr>
                  )}
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-500">{new Date(log.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3">{log.user_id ?? "—"}</td>
                      <td className="px-4 py-3 font-medium">{log.action}</td>
                      <td className="px-4 py-3">{log.entity}</td>
                      <td className="px-4 py-3 text-gray-500">{log.entity_id ?? "—"}</td>
                      <td className="px-4 py-3 text-gray-500">{log.ip_address ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "CMS / Settings" && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">Edit static homepage content and platform settings. Changes are reflected on the landing page immediately.</p>
              {settings.map((s) => (
                <div key={s.key} className="flex flex-col gap-2 rounded-xl border bg-white px-5 py-4 md:flex-row md:items-center">
                  <div className="md:w-64">
                    <p className="font-medium text-gray-900">{s.key}</p>
                    {s.description && <p className="text-xs text-gray-500">{s.description}</p>}
                  </div>
                  <input
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={settingEdits[s.key] ?? ""}
                    onChange={(e) => setSettingEdits((m) => ({ ...m, [s.key]: e.target.value }))}
                  />
                  <Button size="sm" onClick={() => saveSetting(s.key)}>Save</Button>
                </div>
              ))}
            </div>
          )}

          {tab === "Import / Export" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-xl border bg-white p-6 space-y-4">
                <h3 className="font-semibold text-gray-900">Export data</h3>
                <p className="text-sm text-gray-500">Download any dataset as CSV, Excel or JSON.</p>
                <div className="space-y-3">
                  {EXPORTABLE.map((entity) => (
                    <div key={entity} className="flex items-center justify-between">
                      <span className="text-sm capitalize text-gray-700">{entity}</span>
                      <div className="flex gap-2">
                        <Button size="sm" variant="secondary" onClick={() => adminApi.exportEntity(entity, "csv")}>CSV</Button>
                        <Button size="sm" variant="secondary" onClick={() => adminApi.exportEntity(entity, "excel")}>Excel</Button>
                        <Button size="sm" variant="secondary" onClick={() => adminApi.exportEntity(entity, "json")}>JSON</Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border bg-white p-6 space-y-4">
                <h3 className="font-semibold text-gray-900">Import data</h3>
                <p className="text-sm text-gray-500">Upload a CSV or JSON file for users or properties.</p>
                <form onSubmit={runImport} className="space-y-3">
                  <select className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" value={importEntity}
                    onChange={(e) => setImportEntity(e.target.value)}>
                    <option value="users">Users</option>
                    <option value="properties">Properties</option>
                  </select>
                  <input type="file" accept=".csv,.json" onChange={(e) => setImportFile(e.target.files[0])} className="text-sm" />
                  <Button type="submit" loading={importing}>Import</Button>
                </form>
                {importResult && (
                  <div className="rounded-lg bg-gray-50 p-3 text-sm">
                    <p className="text-green-700">Inserted: {importResult.inserted}</p>
                    <p className="text-red-600">Failed: {importResult.failed}</p>
                    {importResult.errors?.slice(0, 5).map((er, i) => (
                      <p key={i} className="text-xs text-gray-500">Row {er.row}: {er.error}</p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  );
}