import { useEffect, useState } from "react";
import { propertyApi } from "../api/propertyApi";
import Input from "./ui/Input";
import Button from "./ui/Button";

export default function FiltersPanel({ filters, onChange }) {
  const [cities, setCities] = useState([]);
  const [amenities, setAmenities] = useState([]);
  const [neighborhoods, setNeighborhoods] = useState([]);

  useEffect(() => {
    propertyApi.getCities().then(({ data }) => setCities(data));
    propertyApi.getAmenities().then(({ data }) => setAmenities(data));
  }, []);

  // Load neighborhoods whenever the selected city changes
  useEffect(() => {
    if (!filters.city_id) { setNeighborhoods([]); return; }
    propertyApi.getNeighborhoods(filters.city_id).then(({ data }) => setNeighborhoods(data));
  }, [filters.city_id]);

  const set = (key, value) => onChange({ ...filters, [key]: value });

  // Changing the city clears any previously-selected neighborhood
  const setCity = (cityId) =>
    onChange({ ...filters, city_id: cityId, neighborhood_id: undefined });

  return (
    <aside className="flex flex-col gap-5 rounded-xl border border-gray-200 bg-white p-5">
      <h2 className="font-semibold text-gray-900">Filters</h2>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">City</label>
        <select
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          value={filters.city_id ?? ""}
          onChange={(e) => setCity(e.target.value || undefined)}
        >
          <option value="">All cities</option>
          {cities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      {filters.city_id && neighborhoods.length > 0 && (
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700">Neighborhood</label>
          <select
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={filters.neighborhood_id ?? ""}
            onChange={(e) => set("neighborhood_id", e.target.value || undefined)}
          >
            <option value="">All neighborhoods</option>
            {neighborhoods.map((n) => <option key={n.id} value={n.id}>{n.name}</option>)}
          </select>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        <Input label="Min price ($)" type="number" min={0} value={filters.min_price ?? ""} onChange={(e) => set("min_price", e.target.value || undefined)} />
        <Input label="Max price ($)" type="number" min={0} value={filters.max_price ?? ""} onChange={(e) => set("max_price", e.target.value || undefined)} />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">Rooms</label>
        <select
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          value={filters.num_rooms ?? ""}
          onChange={(e) => set("num_rooms", e.target.value || undefined)}
        >
          <option value="">Any</option>
          {[1,2,3,4,5,6].map((n) => <option key={n} value={n}>{n}+</option>)}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Input label="Min size (sq ft)" type="number" min={0} value={filters.min_size ?? ""} onChange={(e) => set("min_size", e.target.value || undefined)} />
        <Input label="Max size (sq ft)" type="number" min={0} value={filters.max_size ?? ""} onChange={(e) => set("max_size", e.target.value || undefined)} />
      </div>

      <div className="flex gap-4">
        <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
          <input type="checkbox" checked={filters.is_pet_friendly === true} onChange={(e) => set("is_pet_friendly", e.target.checked)} />
          Pet-friendly
        </label>
      </div>

      {amenities.length > 0 && (
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-gray-700">Amenities</label>
          <div className="flex flex-wrap gap-2">
            {amenities.map((a) => {
              const selected = (filters.amenity_ids ?? []).includes(a.id);
              return (
                <button
                  key={a.id}
                  onClick={() => {
                    const ids = filters.amenity_ids ?? [];
                    set("amenity_ids", selected ? ids.filter((id) => id !== a.id) : [...ids, a.id]);
                  }}
                  className={`rounded-full border px-3 py-1 text-xs transition-colors ${selected ? "border-brand-400 bg-brand-50 text-brand-700" : "border-gray-300 text-gray-600 hover:bg-gray-50"}`}
                >
                  {a.name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <Button variant="secondary" onClick={() => onChange({})}>Clear filters</Button>
    </aside>
  );
}
