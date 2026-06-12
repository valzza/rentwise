import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { propertyApi } from "../api/propertyApi";
import PropertyCard from "../components/PropertyCard";
import Spinner from "../components/ui/Spinner";
import Logo from "../components/Logo";
import { useAuth } from "../hooks/useAuth";

export default function Landing() {
  const { isAuthenticated } = useAuth();
  const [q, setQ] = useState("");
  const [featured, setFeatured] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    propertyApi.getFeatured()
      .then(({ data }) => setFeatured(data))
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    navigate(`/properties?q=${encodeURIComponent(q)}`);
  };

  return (
    <div className="min-h-screen bg-[#f4f5f7]">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200">
        <Logo size="sm" />
        <div className="flex items-center gap-3">
          <Link to="/properties" className="text-sm font-medium text-gray-600 hover:text-brand-600">Browse Properties</Link>
          {isAuthenticated ? (
            <Link to="/dashboard" className="rounded-lg bg-gray-100 border border-gray-300 px-4 py-2 text-sm font-medium text-gray-800 hover:border-brand-300 hover:bg-gray-200 transition-colors">My Dashboard</Link>
          ) : (
            <>
              <Link to="/login" className="text-sm text-gray-600 hover:text-brand-600">Sign in</Link>
              <Link to="/register" className="rounded-lg bg-gray-100 border border-gray-300 px-4 py-2 text-sm font-medium text-gray-800 hover:border-brand-300 hover:bg-gray-200 transition-colors">Get started</Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero — light gray with the logo and teal accents */}
      <section className="relative overflow-hidden border-b border-gray-200 bg-gradient-to-b from-white to-[#eef0f3] px-6 py-20 text-center">
        {/* subtle teal accent shapes */}
        <div className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-brand-100/50 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-brand-100/40 blur-3xl" />

        <div className="relative mx-auto max-w-2xl">
          <div className="mb-6 flex justify-center">
            <Logo size="xl" showTagline />
          </div>
          <h1 className="mb-3 text-3xl md:text-4xl font-bold text-gray-900">
            Find Your Perfect Rental
          </h1>
          <p className="mb-8 text-base text-gray-500">
            AI-powered pricing, real-time updates, and a seamless rental experience across the United States.
          </p>
          <form onSubmit={handleSearch} className="mx-auto flex max-w-lg gap-2">
            <input
              type="text"
              placeholder="Search by title, city, or keyword..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="flex-1 rounded-xl border border-gray-300 bg-white px-5 py-3 text-gray-900 shadow-soft focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
            <button type="submit" className="rounded-xl bg-brand-500 px-6 py-3 font-semibold text-white shadow-soft hover:bg-brand-600 transition-colors">
              Search
            </button>
          </form>
        </div>
      </section>

      {/* Featured */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="mb-6 flex items-center gap-3">
          <span className="h-5 w-1 rounded-full bg-brand-500" />
          <h2 className="text-2xl font-bold text-gray-900">Featured Properties</h2>
        </div>
        {loading ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {featured.map((p) => <PropertyCard key={p.id} property={p} />)}
          </div>
        )}
        <div className="mt-10 text-center">
          <Link to="/properties" className="inline-block rounded-xl border border-brand-300 bg-white px-8 py-3 text-sm font-semibold text-brand-600 hover:bg-brand-50 transition-colors">
            View all properties
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-gray-200 bg-white py-16 px-6">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="mb-10 text-2xl font-bold text-gray-900">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "1", title: "Search Properties", desc: "Filter by city, price, rooms, and amenities to find the right match." },
              { step: "2", title: "Book a Viewing", desc: "Schedule a viewing directly with the landlord at a time that suits you." },
              { step: "3", title: "Apply & Move In", desc: "Submit your rental application, pay the deposit securely, and move in." },
            ].map(({ step, title, desc }) => (
              <div key={step} className="flex flex-col items-center gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-lg font-bold text-brand-600 ring-1 ring-brand-200">{step}</span>
                <h3 className="font-semibold text-gray-900">{title}</h3>
                <p className="text-sm text-gray-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
