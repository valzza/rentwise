import { lazy, Suspense, useState, useEffect } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { bookingApi } from "../../api/bookingApi";
import { applicationApi } from "../../api/applicationApi";
import { paymentApi } from "../../api/paymentApi";
import { propertyApi } from "../../api/propertyApi";
import Badge from "../../components/ui/Badge";
import Spinner from "../../components/ui/Spinner";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import toast from "react-hot-toast";

// Lazy-loaded — pulls in @stripe/react-stripe-js only when payment is triggered
const PaymentModal = lazy(() => import("../../components/PaymentModal"));

const statusColor = { pending: "yellow", confirmed: "green", rejected: "red", cancelled: "gray", approved: "green", withdrawn: "gray", completed: "blue", failed: "red" };
const TABS = ["Bookings", "Applications", "Saved Properties", "Payments"];

export default function TenantDashboard() {
  const [tab, setTab] = useState("Bookings");
  const [bookings, setBookings] = useState([]);
  const [applications, setApplications] = useState([]);
  const [saved, setSaved] = useState([]);
  const [payments, setPayments] = useState([]);
  const [payingLease, setPayingLease] = useState(null);
  const [loading, setLoading] = useState(false);

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
    if (tab === "Payments") {
      setLoading(true);
      paymentApi.listMine({ page: 1, page_size: 20 })
        .then(({ data }) => setPayments(data)).finally(() => setLoading(false));
    }
  }, [tab]);

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
            <p className="text-gray-500 text-sm">Saved properties list — connect to /saved-properties endpoint.</p>
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
