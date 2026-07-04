import { lazy, Suspense, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { propertyApi } from "../api/propertyApi";
import { bookingApi } from "../api/bookingApi";
import { applicationApi } from "../api/applicationApi";
import { savedPropertiesApi } from "../api/savedPropertiesApi";
import { chatApi } from "../api/chatApi";
import { useAuth } from "../hooks/useAuth";
import Spinner from "../components/ui/Spinner";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import PriceEstimateBadge from "../components/PriceEstimateBadge";
import ReviewSection from "../components/ReviewSection";
import Logo from "../components/Logo";
import toast from "react-hot-toast";

// Heavy components — lazy loaded so their vendor chunks stay out of the initial bundle
const ImageGallery = lazy(() => import("../components/ImageGallery"));
const ChatDrawer = lazy(() => import("../components/ChatDrawer"));
const PropertyMap = lazy(() => import("../components/PropertyMap"));

export default function PropertyDetail() {
    const { id } = useParams();
    const { user, isAuthenticated, isTenant, isLandlord } = useAuth();
    const [property, setProperty] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showChat, setShowChat] = useState(false);
    const [chatTenantIds, setChatTenantIds] = useState([]);
    const [selectedTenantId, setSelectedTenantId] = useState(null);
    const [bookingDate, setBookingDate] = useState("");
    const [bookingLoading, setBookingLoading] = useState(false);

    useEffect(() => {
        propertyApi.getById(id)
            .then(({ data }) => setProperty(data))
            .finally(() => setLoading(false));
    }, [id]);

    const isPropertyOwner = isLandlord && user?.id === property?.landlord_id;

    useEffect(() => {
        if (!isPropertyOwner || !property?.id) return;
        chatApi.getPartners(property.id)
            .then(({ data }) => {
                setChatTenantIds(data.tenant_ids ?? []);
                if (data.tenant_ids?.length === 1) {
                    setSelectedTenantId(data.tenant_ids[0]);
                }
            })
            .catch(() => setChatTenantIds([]));
    }, [isPropertyOwner, property?.id]);

    const chatPartnerId = isTenant
        ? property?.landlord_id
        : isPropertyOwner
            ? selectedTenantId
            : property?.landlord_id;

    const canOpenChat = isAuthenticated && (
        (isTenant && property?.landlord_id) ||
        (isPropertyOwner && selectedTenantId) ||
        (!isTenant && !isPropertyOwner && property?.landlord_id)
    );

    const bookViewing = async () => {
        if (!bookingDate) { toast.error("Please select a date and time"); return; }
        setBookingLoading(true);
        try {
            await bookingApi.create({ property_id: property.id, scheduled_at: bookingDate });
            toast.success("Viewing booked! The landlord will confirm soon.");
        } catch (err) {
            toast.error(err.response?.data?.detail ?? "Booking failed");
        } finally {
            setBookingLoading(false);
        }
    };

    const applyForRental = async () => {
        try {
            await applicationApi.create({ property_id: property.id });
            toast.success("Application submitted!");
        } catch (err) {
            toast.error(err.response?.data?.detail ?? "Application failed");
        }
    };

    const toggleSave = async () => {
        try {
            const { data } = await savedPropertiesApi.toggle(property.id);
            toast.success(data.saved ? "Saved to favorites" : "Removed from favorites");
        } catch {
            toast.error("Could not update favorites");
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center"><Spinner size="lg" /></div>;
    if (!property) return <div className="flex h-screen items-center justify-center text-gray-500">Property not found.</div>;

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200">
                <a href="/"><Logo size="sm" /></a>
                <Button variant="ghost" onClick={() => window.history.back()}>← Back</Button>
            </nav>

            <div className="max-w-5xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left: gallery + details */}
                <div className="lg:col-span-2 space-y-6">
                    <Suspense fallback={<div className="aspect-video rounded-xl bg-gray-200 animate-pulse" />}>
                        <ImageGallery images={property.images ?? []} />
                    </Suspense>

                    <div>
                        <div className="flex items-start justify-between gap-3">
                            <h1 className="text-2xl font-bold text-gray-900">{property.title}</h1>
                            <Badge color={property.status === "active" ? "green" : "gray"}>{property.status}</Badge>
                        </div>
                        {property.neighborhood && (
                            <p className="mt-1 flex items-center gap-1 text-sm text-brand-600">
                                📍 {property.neighborhood.name}
                            </p>
                        )}
                        <p className="mt-1 text-sm text-gray-500">
                            {property.num_rooms} rooms · {property.num_bathrooms} bathrooms · {property.size_m2} sq ft
                            {property.is_pet_friendly && " · Pet-friendly"}
                        </p>
                    </div>

                    {property.description && (
                        <p className="text-sm text-gray-700 leading-relaxed">{property.description}</p>
                    )}

                    {property.amenities?.length > 0 && (
                        <div>
                            <h3 className="font-semibold text-gray-900 mb-2">Amenities</h3>
                            <div className="flex flex-wrap gap-2">
                                {property.amenities.map((a) => (
                                    <span key={a.id} className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-700">{a.name}</span>
                                ))}
                            </div>
                        </div>
                    )}

                    {property.neighborhood?.latitude != null && (
                        <div>
                            <h3 className="font-semibold text-gray-900 mb-2">Location</h3>
                            <Suspense fallback={<div className="h-64 rounded-xl bg-gray-200 animate-pulse" />}>
                                <PropertyMap properties={[property]} height="280px" single />
                            </Suspense>
                        </div>
                    )}

                    <div className="border-t border-gray-200 pt-6">
                        <ReviewSection propertyId={property.id} />
                    </div>
                </div>

                {/* Right: pricing + actions */}
                <div className="space-y-4">
                    <div className="rounded-xl border border-gray-200 bg-white p-5 space-y-4 shadow-soft">
                        <p className="text-3xl font-bold text-brand-600">
                            ${Number(property.price).toLocaleString()}
                            <span className="text-sm font-normal text-gray-500">/mo</span>
                        </p>

                        {/* AI price estimate — shown to landlords */}
                        {isLandlord && <PriceEstimateBadge property={property} />}

                        {isTenant && property.status === "active" && (
                            <>
                                <div className="flex flex-col gap-1">
                                    <label className="text-sm font-medium text-gray-700">Pick viewing date & time</label>
                                    <input
                                        type="datetime-local"
                                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                        value={bookingDate}
                                        onChange={(e) => setBookingDate(e.target.value)}
                                    />
                                </div>
                                <Button onClick={bookViewing} loading={bookingLoading} className="w-full">Book a Viewing</Button>
                                <Button variant="secondary" onClick={applyForRental} className="w-full">Apply for Rental</Button>
                                <Button variant="ghost" onClick={toggleSave} className="w-full">♡ Save to favorites</Button>
                            </>
                        )}

                        {isPropertyOwner && chatTenantIds.length > 0 && (
                            <div className="flex flex-col gap-1">
                                <label className="text-sm font-medium text-gray-700">Chat with tenant</label>
                                <select
                                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                    value={selectedTenantId ?? ""}
                                    onChange={(e) => setSelectedTenantId(Number(e.target.value))}
                                >
                                    <option value="" disabled>Select tenant…</option>
                                    {chatTenantIds.map((tid) => (
                                        <option key={tid} value={tid}>Tenant #{tid}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {isPropertyOwner && chatTenantIds.length === 0 && (
                            <p className="text-xs text-gray-500">No tenant messages yet for this listing.</p>
                        )}

                        {canOpenChat && (
                            <Button variant="ghost" onClick={() => setShowChat((v) => !v)} className="w-full">
                                💬 {showChat ? "Close Chat" : isPropertyOwner ? "Open Messages" : "Message Landlord"}
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            {/* Chat drawer — lazy loaded */}
            {showChat && chatPartnerId && (
                <Suspense fallback={null}>
                    <ChatDrawer
                        property={property}
                        otherUserId={chatPartnerId}
                        onClose={() => setShowChat(false)}
                    />
                </Suspense>
            )}
        </div>
    );
}