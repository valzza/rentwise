import { useEffect } from "react";
import { usePriceEstimate } from "../hooks/usePriceEstimate";
import Spinner from "./ui/Spinner";

export default function PriceEstimateBadge({ property }) {
  const { estimate, loading, error, fetchEstimate } = usePriceEstimate();

  useEffect(() => {
    if (!property) return;
    fetchEstimate({
      city_id: property.city_id,
      neighborhood_id: property.neighborhood_id ?? undefined,
      size_m2: property.size_m2,
      num_rooms: property.num_rooms,
      num_bathrooms: property.num_bathrooms,
      is_pet_friendly: property.is_pet_friendly,
      amenities_count: property.amenities?.length ?? 0,
      property_id: property.id,
    });
  }, [property?.id]);

  if (loading) return <div className="flex items-center gap-2 text-sm text-gray-500"><Spinner size="sm" /> Calculating AI price...</div>;
  if (error) return <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700">AI estimate unavailable: {error}</div>;
  if (!estimate) return null;

  return (
    <div className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-brand-600 mb-1">AI Price Estimate</p>
      <p className="text-lg font-bold text-brand-700">
        ${estimate.min_price.toLocaleString()} – ${estimate.max_price.toLocaleString()}
        <span className="ml-2 text-xs font-normal text-brand-500">/ month</span>
      </p>
      <p className="text-xs text-brand-500 mt-0.5">Suggested: ${estimate.suggested_price.toLocaleString()}</p>
    </div>
  );
}
