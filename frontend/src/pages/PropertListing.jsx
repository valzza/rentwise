import { lazy, Suspense, useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { propertyApi } from "../api/propertyApi";
import PropertyCard from "../components/PropertyCard";
import FiltersPanel from "../components/FiltersPanel";
import Spinner from "../components/ui/Spinner";
import Logo from "../components/Logo";
import { useAuth } from "../hooks/useAuth";

// Lazy — pulls in leaflet (vendor-map) only when the map view is opened
const PropertyMap = lazy(() => import("../components/PropertyMap"));

export default function PropertyListing() {
    const { isAuthenticated } = useAuth();
    const [searchParams, setSearchParams] = useSearchParams();
    const [view, setView] = useState("grid");
    const [properties, setProperties] = useState([]);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(1);
    const [loading, setLoading] = useState(false);

    const RESERVED = ["page", "sort_by", "sort_order"];
    const BOOL_KEYS = ["is_pet_friendly"];

    // Derive filters from URL so links are shareable.
    // Booleans are parsed to real booleans and amenity_ids collected into a
    // number array — so checkboxes/chips reflect state and round-trip correctly.
    const getFilters = () => {
        const f = {};
        for (const [k, v] of searchParams.entries()) {
            if (RESERVED.includes(k) || k === "amenity_ids") continue;
            f[k] = BOOL_KEYS.includes(k) ? v === "true" : v;
        }
        const amenityIds = searchParams.getAll("amenity_ids").map(Number);
        if (amenityIds.length) f.amenity_ids = amenityIds;
        return f;
    };

    const page = parseInt(searchParams.get("page") ?? "1");
    const sort_by = searchParams.get("sort_by") ?? "created_at";
    const sort_order = searchParams.get("sort_order") ?? "desc";

    useEffect(() => {
        setLoading(true);
        const params = { ...getFilters(), page, sort_by, sort_order, page_size: 12 };
        propertyApi.search(params)
            .then(({ data }) => { setProperties(data.items); setTotal(data.total); setPages(data.pages); })
            .finally(() => setLoading(false));
    }, [searchParams.toString()]);

    // Serialize filters to the URL: skip unset/false/empty values, and write
    // arrays as repeated keys. This prevents `undefined` becoming the string
    // "undefined" and lets filters be turned off again.
    const updateFilters = (filters) => {
        const next = new URLSearchParams();
        for (const [k, v] of Object.entries(filters)) {
            if (v === undefined || v === null || v === "" || v === false) continue;
            if (Array.isArray(v)) {
                v.forEach((item) => next.append(k, item));
            } else {
                next.append(k, v);
            }
        }
        next.set("page", "1");
        next.set("sort_by", sort_by);
        next.set("sort_order", sort_order);
        setSearchParams(next);
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200">
                <Link to="/"><Logo size="sm" /></Link>
                <div className="flex items-center gap-4">
                    <Link to="/properties" className="text-sm font-medium text-brand-600">Properties</Link>
                    {isAuthenticated ? (
                        <Link to="/dashboard" className="rounded-lg bg-gray-100 border border-gray-300 px-4 py-2 text-sm font-medium text-gray-800 hover:border-brand-300 hover:bg-gray-200 transition-colors">
                            My Dashboard
                        </Link>
                    ) : (
                        <Link to="/login" className="text-sm text-gray-600 hover:text-brand-600">Sign in</Link>
                    )}
                </div>
            </nav>

            <div className="max-w-7xl mx-auto px-6 py-8 flex gap-6">
                {/* Sidebar */}
                <div className="w-72 flex-shrink-0 hidden md:block">
                    <FiltersPanel filters={getFilters()} onChange={updateFilters} />
                </div>

                {/* Results */}
                <div className="flex-1">
                    <div className="mb-4 flex items-center justify-between">
                        <p className="text-sm text-gray-600">{total} properties found</p>
                        <div className="flex items-center gap-2">
                            {/* Grid / Map toggle */}
                            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
                                <button
                                    onClick={() => setView("grid")}
                                    className={`px-3 py-1.5 text-sm font-medium transition-colors ${view === "grid" ? "bg-brand-500 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
                                >
                                    Grid
                                </button>
                                <button
                                    onClick={() => setView("map")}
                                    className={`px-3 py-1.5 text-sm font-medium transition-colors ${view === "map" ? "bg-brand-500 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
                                >
                                    Map
                                </button>
                            </div>
                            <select
                                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
                                value={`${sort_by}-${sort_order}`}
                                onChange={(e) => {
                                    const [sb, so] = e.target.value.split("-");
                                    setSearchParams((p) => { p.set("sort_by", sb); p.set("sort_order", so); return p; });
                                }}
                            >
                                <option value="created_at-desc">Newest</option>
                                <option value="price-asc">Price: Low to High</option>
                                <option value="price-desc">Price: High to Low</option>
                                <option value="rating-desc">Top Rated</option>
                            </select>
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
                    ) : view === "map" ? (
                        <Suspense fallback={<div className="flex justify-center py-20"><Spinner size="lg" /></div>}>
                            <PropertyMap properties={properties} height="600px" />
                        </Suspense>
                    ) : (
                        <>
                            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
                                {properties.map((p) => <PropertyCard key={p.id} property={p} />)}
                            </div>
                            {properties.length === 0 && (
                                <p className="py-20 text-center text-gray-500">No properties match your filters.</p>
                            )}

                            {/* Pagination */}
                            {pages > 1 && (
                                <div className="mt-8 flex justify-center gap-2">
                                    {Array.from({ length: pages }, (_, i) => i + 1).map((p) => (
                                        <button
                                            key={p}
                                            onClick={() => setSearchParams((sp) => { sp.set("page", p); return sp; })}
                                            className={`rounded-lg px-4 py-2 text-sm transition-colors ${page === p ? "bg-brand-500 text-white" : "bg-white border border-gray-200 text-gray-600 hover:border-brand-300"}`}
                                        >
                                            {p}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
