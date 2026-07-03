import { lazy, Suspense, useState, useEffect } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { bookingApi } from "../../api/bookingApi";
import { applicationApi } from "../../api/applicationApi";
import { paymentApi } from "../../api/paymentApi";
import { leaseApi } from "../../api/leaseApi";
import { maintenanceApi } from "../../api/maintenanceApi";
import { savedPropertiesApi } from "../../api/savedPropertiesApi";
import PropertyCard from "../../components/PropertyCard";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import toast from "react-hot-toast";

// Lazy-loaded — pulls in @stripe/react-stripe-js only when payment is triggered
const PaymentModal = lazy(() => import("../../components/PaymentModal"));

const statusColor = { pending: "yellow", confirmed: "green", rejected: "red", cancelled: "gray", approved: "green", withdrawn: "gray", completed: "blue", failed: "red", active: "green", in_progress: "blue", resolved: "green", closed: "gray" };
const TABS = ["Bookings", "Applications", "Leases", "Maintenance", "Saved Properties", "Payments"];

export default function TenantDashboard() {
  const [tab, setTab] = useState("Bookings");
  const [bookings, setBookings] = useState([]);
  const [applications, setApplications] = useState([]);
  const [leases, setLeases] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [saved, setSaved] = useState([]);
  const [payments, setPayments] = useState([]);
  const [payingLease, setPayingLease] = useState(null);
  const [loading, setLoading] = useState(false);

  // Maintenance request form
  const [maintForm, setMaintForm] = useState({ property_id: "", title: "", description: "", priority: "medium" });
  const [submittingMaint, setSubmittingMaint] = useState(false);

  const loadLeases = () => leaseApi.list().then(({ data }) => setLeases(data));
  const loadMaintenance = () => maintenanceApi.listMine().then(({ data }) => setMaintenance(data));

  useEffect(() => {
    if (tab === "Bookings") {
      setLoading(true);
      bookingApi.list({ role: "tenant", page: 1, page_size: 20 })
        .then(({ data }) => setBookings(data.items)).finally(() => setLoading(false));
    }
    if (tab === "Applications") {
      setLoading(true);
      applicationApi.listMine({ page: 1, page_size: 20 })
        .then(({ data }) => setApplications(data.items)).finally(() => setLoading(false));
    }
    if (tab === "Leases") {
      setLoading(true);
      loadLeases().finally(() => setLoading(false));
    }
    if (tab === "Maintenance") {
      setLoading(true);
      loadMaintenance().finally(() => setLoading(false));
    }
    if (tab === "Saved Properties") {
      setLoading(true);
      savedPropertiesApi.list().then(({ data }) => setSaved(data)).finally(() => setLoading(false));
    }
    if (tab === "Payments") {
      setLoading(true);
      paymentApi.listMine({ page: 1, page_size: 20 })
        .then(({ data }) => setPayments(data)).finally(() => setLoading(false));
    }
  }, [tab]);

  const submitMaintenance = async (e) => {
    e.preventDefault();
    setSubmittingMaint(true);
    try {
      await maintenanceApi.create({
        property_id: parseInt(maintForm.property_id),
        title: maintForm.title,
        description: maintForm.description,
        priority: maintForm.priority,
      });
      toast.success("Maintenance request submitted");
      setMaintForm({ property_id: "", title: "", description: "", priority: "medium" });
      loadMaintenance();
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Could not submit request");
    } finally {
      setSubmittingMaint(false);
    }
  };

  return (
    <DashboardLayout>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">My Dashboard</h1>

      {/* Tab nav */}
      <div className="flex gap-1 border-b mb-6">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${tab === t ? "border-brand-500 text-brand-600" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {t}
          </button>
        ))}
      </div>

      {loading ? <div className="flex justify-center py-12"><Spinner size="lg" /></div> : (
        <>
          {tab === "Bookings" && (
            <div className="space-y-3">
              {bookings.length === 0 && <p className="text-gray-500 text-sm">No bookings yet.</p>}
              {bookings.map((b) => (
                <div key={b.id} className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">Property #{b.property_id}</p>
                    <p className="text-xs text-gray-500">{new Date(b.scheduled_at).toLocaleString()}</p>
                  </div>
                  <Badge color={statusColor[b.status] ?? "gray"}>{b.status}</Badge>
                </div>
              ))}
            </div>
          )}

          {tab === "Applications" && (
            <div className="space-y-3">
              {applications.length === 0 && <p className="text-gray-500 text-sm">No applications yet.</p>}
              {applications.map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">Property #{a.property_id}</p>
                    <p className="text-xs text-gray-500">Submitted {new Date(a.created_at).toLocaleDateString()}</p>
                  </div>
                  <Badge color={statusColor[a.status] ?? "gray"}>{a.status}</Badge>
                </div>
              ))}
            </div>
          )}

          {tab === "Leases" && (
            <div className="space-y-3">
              {leases.length === 0 && <p className="text-gray-500 text-sm">No leases yet.</p>}
              {leases.map((l) => (
                <div key={l.id} className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">Lease #{l.id} — Property #{l.property_id}</p>
                    <p className="text-xs text-gray-500">{l.start_date} → {l.end_date} · ${Number(l.monthly_rent).toLocaleString()}/mo · Deposit ${Number(l.deposit_amount).toLocaleString()}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge color={statusColor[l.status] ?? "gray"}>{l.status}</Badge>
                    <Button size="sm" onClick={() => setPayingLease(l)}>Pay Deposit</Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "Maintenance" && (
            <div className="space-y-6">
              <form onSubmit={submitMaintenance} className="rounded-xl border bg-white p-5 space-y-4">
                <h3 className="font-semibold text-gray-900">Report an Issue</h3>
                <div className="grid grid-cols-2 gap-3">
                  <Input label="Property ID" type="number" value={maintForm.property_id} onChange={(e) => setMaintForm((f) => ({ ...f, property_id: e.target.value }))} required />
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Priority</label>
                    <select className="rounded-lg border border-gray-300 px-3 py-2 text-sm" value={maintForm.priority}
                      onChange={(e) => setMaintForm((f) => ({ ...f, priority: e.target.value }))}>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                </div>
                <Input label="Title" value={maintForm.title} onChange={(e) => setMaintForm((f) => ({ ...f, title: e.target.value }))} required />
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Description</label>
                  <textarea className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" rows={3}
                    value={maintForm.description} onChange={(e) => setMaintForm((f) => ({ ...f, description: e.target.value }))} required />
                </div>
                <Button type="submit" loading={submittingMaint}>Submit request</Button>
              </form>

              <div className="space-y-3">
                {maintenance.length === 0 && <p className="text-gray-500 text-sm">No maintenance requests yet.</p>}
                {maintenance.map((m) => (
                  <div key={m.id} className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4">
                    <div>
                      <p className="font-medium text-gray-900">{m.title} <span className="text-xs text-gray-400">(Property #{m.property_id})</span></p>
                      <p className="text-xs text-gray-500">{m.description}</p>
                      <p className="text-xs text-gray-400">Priority: {m.priority}</p>
                    </div>
                    <Badge color={statusColor[m.status] ?? "gray"}>{m.status}</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === "Payments" && (
            <div className="space-y-3">
              {payments.length === 0 && <p className="text-gray-500 text-sm">No payments yet.</p>}
              {payments.map((p) => (
                <div key={p.id} className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">${Number(p.amount).toLocaleString()} — {p.type}</p>
                    <p className="text-xs text-gray-500">{new Date(p.created_at).toLocaleDateString()}</p>
                  </div>
                  <Badge color={statusColor[p.status] ?? "gray"}>{p.status}</Badge>
                </div>
              ))}
            </div>
          )}

          {tab === "Saved Properties" && (
            <div>
              {saved.length === 0 ? (
                <p className="text-gray-500 text-sm">No saved properties yet. Tap the heart on any listing to save it.</p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {saved.map((p) => (
                    <PropertyCard
                      key={p.id}
                      property={p}
                      initialSaved
                      onUnsave={(id) => setSaved((s) => s.filter((x) => x.id !== id))}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Payment modal — only loads Stripe bundle when triggered */}
      {payingLease && (
        <Modal open onClose={() => setPayingLease(null)} title="Pay Deposit">
          <Suspense fallback={<Spinner />}>
            <PaymentModal lease={payingLease} onSuccess={() => setPayingLease(null)} onClose={() => setPayingLease(null)} />
          </Suspense>
        </Modal>
      )}
    </DashboardLayout>
  );
}