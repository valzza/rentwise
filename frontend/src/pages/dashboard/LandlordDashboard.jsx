import { lazy, Suspense, useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { bookingApi } from "../../api/bookingApi";
import { applicationApi } from "../../api/applicationApi";
import { paymentApi } from "../../api/paymentApi";
import { propertyApi } from "../../api/propertyApi";
import { leaseApi } from "../../api/leaseApi";
import { maintenanceApi } from "../../api/maintenanceApi";
import { fileApi } from "../../api/fileApi";
import { useAuth } from "../../hooks/useAuth";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Spinner from "../../components/ui/Spinner";
import toast from "react-hot-toast";

// Lazy — pulls in recharts (vendor-charts) only when Earnings tab is viewed
const EarningsChart = lazy(() => import("../../components/EarningsChart"));
const PriceEstimatorTool = lazy(() => import("../../components/PriceEstimatorTool"));

const statusColor = { pending: "yellow", confirmed: "green", rejected: "red", approved: "green", in_progress: "blue", resolved: "green", closed: "gray", active: "green" };
const TABS = ["My Properties", "Bookings", "Applications", "Leases", "Maintenance", "Earnings", "AI Price Estimator"];

export default function LandlordDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("My Properties");
  const [properties, setProperties] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [applications, setApplications] = useState([]);
  const [appStatusFilter, setAppStatusFilter] = useState("");
  const [leases, setLeases] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [maintFilter, setMaintFilter] = useState({ status: "", priority: "" });
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(false);

  // Create property modal state
  const [showCreate, setShowCreate] = useState(false);
  const [newProp, setNewProp] = useState({ title: "", description: "", price: "", city_id: "", size_m2: "", num_rooms: "", num_bathrooms: "", is_pet_friendly: false });
  const [images, setImages] = useState([]);
  const [bulletPoints, setBulletPoints] = useState("");
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [cities, setCities] = useState([]);

  // Create lease form state
  const [leaseForm, setLeaseForm] = useState({ property_id: "", tenant_id: "", start_date: "", end_date: "", monthly_rent: "", deposit_amount: "" });
  const [creatingLease, setCreatingLease] = useState(false);

  useEffect(() => {
    propertyApi.getCities().then(({ data }) => setCities(data));
  }, []);

  const handleGenerate = async () => {
    if (!bulletPoints.trim()) return toast.error("Enter some bullet points first.");
    setGenerating(true);
    try {
      const { data } = await propertyApi.generateDescription(bulletPoints);
      setNewProp((p) => ({ ...p, description: data.description }));
      toast.success("Description generated!");
    } catch {
      toast.error("Generation failed. Check your Anthropic API key.");
    } finally {
      setGenerating(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const { data: created } = await propertyApi.create({
        ...newProp,
        price: parseFloat(newProp.price),
        city_id: parseInt(newProp.city_id),
        size_m2: parseFloat(newProp.size_m2),
        num_rooms: parseInt(newProp.num_rooms),
        num_bathrooms: parseInt(newProp.num_bathrooms),
      });

      // Upload selected images and link them to the new property
      if (images.length && created?.id) {
        for (const img of images) {
          await fileApi.upload(img, { entity: "property", entityId: created.id, linkProperty: true });
        }
      }

      toast.success("Property created!");
      setShowCreate(false);
      setNewProp({ title: "", description: "", price: "", city_id: "", size_m2: "", num_rooms: "", num_bathrooms: "", is_pet_friendly: false });
      setImages([]);
      setBulletPoints("");
      propertyApi.search({ page: 1, page_size: 20 }).then(({ data }) => setProperties(data.items));
    } catch {
      toast.error("Failed to create property.");
    } finally {
      setSaving(false);
    }
  };

  const togglePropertyStatus = async (p) => {
    const next = p.status === "active" ? "inactive" : "active";
    try {
      await propertyApi.update(p.id, { status: next });
      setProperties((ps) => ps.map((x) => x.id === p.id ? { ...x, status: next } : x));
      toast.success(`Property marked ${next}`);
    } catch { toast.error("Update failed"); }
  };

  const deleteProperty = async (id) => {
    if (!window.confirm("Delete this property? This cannot be undone.")) return;
    try {
      await propertyApi.remove(id);
      setProperties((ps) => ps.filter((x) => x.id !== id));
      toast.success("Property deleted");
    } catch { toast.error("Delete failed"); }
  };

  const createLease = async (e) => {
    e.preventDefault();
    setCreatingLease(true);
    try {
      await leaseApi.create({
        property_id: parseInt(leaseForm.property_id),
        tenant_id: parseInt(leaseForm.tenant_id),
        start_date: leaseForm.start_date,
        end_date: leaseForm.end_date,
        monthly_rent: parseFloat(leaseForm.monthly_rent),
        deposit_amount: parseFloat(leaseForm.deposit_amount),
      });
      toast.success("Lease created!");
      setLeaseForm({ property_id: "", tenant_id: "", start_date: "", end_date: "", monthly_rent: "", deposit_amount: "" });
      leaseApi.list().then(({ data }) => setLeases(data));
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Failed to create lease");
    } finally {
      setCreatingLease(false);
    }
  };

  const updateMaintStatus = async (id, status) => {
    try {
      await maintenanceApi.updateStatus(id, { status });
      setMaintenance((ms) => ms.map((m) => m.id === id ? { ...m, status } : m));
      toast.success(`Marked ${status}`);
    } catch { toast.error("Update failed"); }
  };

  useEffect(() => {
    if (tab === "My Properties") {
      setLoading(true);
      propertyApi.search({ page: 1, page_size: 20 })
        .then(({ data }) => setProperties(data.items)).finally(() => setLoading(false));
    }
    if (tab === "Bookings") {
      setLoading(true);
      bookingApi.list({ role: "landlord", page: 1, page_size: 20 })
        .then(({ data }) => setBookings(data.items)).finally(() => setLoading(false));
    }
    if (tab === "Applications") {
      setLoading(true);
      applicationApi.listLandlord({ status: appStatusFilter || undefined, page: 1, page_size: 20 })
        .then(({ data }) => setApplications(data.items)).finally(() => setLoading(false));
    }
    if (tab === "Leases") {
      setLoading(true);
      leaseApi.list().then(({ data }) => setLeases(data)).finally(() => setLoading(false));
    }
    if (tab === "Maintenance") {
      setLoading(true);
      maintenanceApi.listLandlord({ status: maintFilter.status || undefined, priority: maintFilter.priority || undefined })
        .then(({ data }) => setMaintenance(data)).finally(() => setLoading(false));
    }
    if (tab === "Earnings") {
      setLoading(true);
      paymentApi.getEarnings()
        .then(({ data }) => setEarnings(data)).finally(() => setLoading(false));
    }
  }, [tab, appStatusFilter, maintFilter]);

  const updateBookingStatus = async (id, status) => {
    try {
      await bookingApi.updateStatus(id, status);
      setBookings((bs) => bs.map((b) => b.id === id ? { ...b, status } : b));
      toast.success(`Booking ${status}`);
    } catch { toast.error("Update failed"); }
  };

  const updateAppStatus = async (id, status) => {
    try {
      await applicationApi.updateStatus(id, status);
      setApplications((as) => as.map((a) => a.id === id ? { ...a, status } : a));
      toast.success(`Application ${status}`);
    } catch { toast.error("Update failed"); }
  };

  return (
    <DashboardLayout>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">Landlord Dashboard</h1>

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
          {tab === "My Properties" && (
            <div className="space-y-3">
              <div className="flex justify-end">
                <Button onClick={() => setShowCreate(true)}>+ New Property</Button>
              </div>
              {properties.length === 0 && <p className="text-gray-500 text-sm">No properties yet.</p>}
              {properties.map((p) => (
                <div key={p.id} className="flex items-center justify-between rounded-xl border bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">{p.title}</p>
                    <p className="text-xs text-gray-500">${Number(p.price).toLocaleString()}/mo · {p.num_rooms} rooms</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge color={p.status === "active" ? "green" : "gray"}>{p.status}</Badge>
                    <Button size="sm" variant="secondary" onClick={() => togglePropertyStatus(p)}>
                      {p.status === "active" ? "Deactivate" : "Activate"}
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => deleteProperty(p.id)}>Delete</Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "Bookings" && (
            <div className="space-y-3">
              {bookings.length === 0 && <p className="text-gray-500 text-sm">No bookings received.</p>}
              {bookings.map((b) => (
                <div key={b.id} className="flex items-center justify-between rounded-xl border bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">Tenant #{b.tenant_id} — Property #{b.property_id}</p>
                    <p className="text-xs text-gray-500">{new Date(b.scheduled_at).toLocaleString()}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge color={statusColor[b.status] ?? "gray"}>{b.status}</Badge>
                    {b.status === "pending" && (
                      <>
                        <Button size="sm" onClick={() => updateBookingStatus(b.id, "confirmed")}>Confirm</Button>
                        <Button size="sm" variant="danger" onClick={() => updateBookingStatus(b.id, "rejected")}>Reject</Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "Applications" && (
            <div className="space-y-3">
              <div className="flex justify-end">
                <select
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={appStatusFilter}
                  onChange={(e) => setAppStatusFilter(e.target.value)}
                >
                  <option value="">All statuses</option>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              {applications.length === 0 && <p className="text-gray-500 text-sm">No applications.</p>}
              {applications.map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-xl border bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">Tenant #{a.tenant_id} — Property #{a.property_id}</p>
                    <p className="text-xs text-gray-500">{a.message ?? "No message"}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge color={statusColor[a.status] ?? "gray"}>{a.status}</Badge>
                    {a.status === "pending" && (
                      <>
                        <Button size="sm" onClick={() => updateAppStatus(a.id, "approved")}>Approve</Button>
                        <Button size="sm" variant="danger" onClick={() => updateAppStatus(a.id, "rejected")}>Reject</Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "Leases" && (
            <div className="space-y-6">
              <form onSubmit={createLease} className="rounded-xl border bg-white p-5 space-y-4">
                <h3 className="font-semibold text-gray-900">Create a Lease</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Property</label>
                    <select
                      className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      value={leaseForm.property_id}
                      onChange={(e) => setLeaseForm((f) => ({ ...f, property_id: e.target.value }))}
                      required
                    >
                      <option value="">Select a property</option>
                      {properties.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
                    </select>
                  </div>
                  <Input label="Tenant ID" type="number" value={leaseForm.tenant_id} onChange={(e) => setLeaseForm((f) => ({ ...f, tenant_id: e.target.value }))} required />
                  <Input label="Start date" type="date" value={leaseForm.start_date} onChange={(e) => setLeaseForm((f) => ({ ...f, start_date: e.target.value }))} required />
                  <Input label="End date" type="date" value={leaseForm.end_date} onChange={(e) => setLeaseForm((f) => ({ ...f, end_date: e.target.value }))} required />
                  <Input label="Monthly rent ($)" type="number" value={leaseForm.monthly_rent} onChange={(e) => setLeaseForm((f) => ({ ...f, monthly_rent: e.target.value }))} required />
                  <Input label="Deposit ($)" type="number" value={leaseForm.deposit_amount} onChange={(e) => setLeaseForm((f) => ({ ...f, deposit_amount: e.target.value }))} required />
                </div>
                <p className="text-xs text-gray-400">Tip: the tenant ID is shown on each rental application.</p>
                <Button type="submit" loading={creatingLease}>Create Lease</Button>
              </form>

              <div className="space-y-3">
                {leases.length === 0 && <p className="text-gray-500 text-sm">No leases yet.</p>}
                {leases.map((l) => (
                  <div key={l.id} className="flex items-center justify-between rounded-xl border bg-white px-5 py-4">
                    <div>
                      <p className="font-medium text-gray-900">Lease #{l.id} — Property #{l.property_id}</p>
                      <p className="text-xs text-gray-500">Tenant #{l.tenant_id} · {l.start_date} → {l.end_date} · ${Number(l.monthly_rent).toLocaleString()}/mo</p>
                    </div>
                    <Badge color={statusColor[l.status] ?? "gray"}>{l.status}</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === "Maintenance" && (
            <div className="space-y-3">
              <div className="flex justify-end gap-2">
                <select className="rounded-lg border border-gray-300 px-3 py-2 text-sm" value={maintFilter.status}
                  onChange={(e) => setMaintFilter((f) => ({ ...f, status: e.target.value }))}>
                  <option value="">All statuses</option>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
                <select className="rounded-lg border border-gray-300 px-3 py-2 text-sm" value={maintFilter.priority}
                  onChange={(e) => setMaintFilter((f) => ({ ...f, priority: e.target.value }))}>
                  <option value="">All priorities</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              {maintenance.length === 0 && <p className="text-gray-500 text-sm">No maintenance requests.</p>}
              {maintenance.map((m) => (
                <div key={m.id} className="flex items-center justify-between rounded-xl border bg-white px-5 py-4">
                  <div>
                    <p className="font-medium text-gray-900">{m.title} <span className="text-xs text-gray-400">(Property #{m.property_id})</span></p>
                    <p className="text-xs text-gray-500">{m.description}</p>
                    <p className="text-xs text-gray-400">Priority: {m.priority}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge color={statusColor[m.status] ?? "gray"}>{m.status}</Badge>
                    {m.status !== "resolved" && m.status !== "closed" && (
                      <>
                        <Button size="sm" onClick={() => updateMaintStatus(m.id, "in_progress")}>Start</Button>
                        <Button size="sm" variant="secondary" onClick={() => updateMaintStatus(m.id, "resolved")}>Resolve</Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "Earnings" && (
            <div className="space-y-4">
              {earnings && (
                <>
                  <div className="rounded-xl border bg-white px-6 py-4">
                    <p className="text-sm text-gray-500">Total Revenue</p>
                    <p className="text-3xl font-bold text-brand-600">${Number(earnings.total_earned).toLocaleString()}</p>
                  </div>
                  <div className="rounded-xl border bg-white p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Monthly Earnings</h3>
                    <Suspense fallback={<Spinner />}>
                      <EarningsChart data={earnings.monthly} />
                    </Suspense>
                  </div>
                </>
              )}
            </div>
          )}

          {tab === "AI Price Estimator" && (
            <Suspense fallback={<div className="flex justify-center py-12"><Spinner size="lg" /></div>}>
              <PriceEstimatorTool />
            </Suspense>
          )}
        </>
      )}
      {/* Create Property Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-900">Create New Property</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600 text-xl font-bold">×</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <Input label="Title" value={newProp.title} onChange={(e) => setNewProp((p) => ({ ...p, title: e.target.value }))} required />

              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">City</label>
                <select
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={newProp.city_id}
                  onChange={(e) => setNewProp((p) => ({ ...p, city_id: e.target.value }))}
                  required
                >
                  <option value="">Select a city</option>
                  {cities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Input label="Price ($/mo)" type="number" min="0" value={newProp.price} onChange={(e) => setNewProp((p) => ({ ...p, price: e.target.value }))} required />
                <Input label="Size (sq ft)" type="number" min="0" value={newProp.size_m2} onChange={(e) => setNewProp((p) => ({ ...p, size_m2: e.target.value }))} required />
                <Input label="Rooms" type="number" min="1" value={newProp.num_rooms} onChange={(e) => setNewProp((p) => ({ ...p, num_rooms: e.target.value }))} required />
                <Input label="Bathrooms" type="number" min="1" value={newProp.num_bathrooms} onChange={(e) => setNewProp((p) => ({ ...p, num_bathrooms: e.target.value }))} required />
              </div>

              <div className="flex gap-6">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={newProp.is_pet_friendly} onChange={(e) => setNewProp((p) => ({ ...p, is_pet_friendly: e.target.checked }))} />
                  Pet-friendly
                </label>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Photos</label>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => setImages(Array.from(e.target.files))}
                  className="text-sm"
                />
                {images.length > 0 && <p className="text-xs text-gray-500">{images.length} image(s) selected — the first becomes the cover photo.</p>}
              </div>

              {/* AI Description Generator */}
              <div className="rounded-xl border border-brand-200 bg-brand-50 p-4 space-y-3">
                <p className="text-sm font-medium text-brand-700">AI Description Generator</p>
                <textarea
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm resize-none"
                  rows={3}
                  placeholder="e.g. 2 rooms, balcony, near downtown, quiet street, pet-friendly"
                  value={bulletPoints}
                  onChange={(e) => setBulletPoints(e.target.value)}
                />
                <Button type="button" variant="secondary" onClick={handleGenerate} disabled={generating}>
                  {generating ? "Generating..." : "Generate description with AI"}
                </Button>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Description</label>
                <textarea
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm resize-none"
                  rows={4}
                  placeholder="Property description..."
                  value={newProp.description}
                  onChange={(e) => setNewProp((p) => ({ ...p, description: e.target.value }))}
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Create Property"}</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}