import { useEffect, useState } from "react";
import { propertyApi } from "../api/propertyApi";
import { mlApi } from "../api/mlApi";
import Input from "./ui/Input";
import Button from "./ui/Button";
import Spinner from "./ui/Spinner";
import toast from "react-hot-toast";

const initialForm = {
  city_id: "",
  size_m2: 900,
  num_rooms: 2,
  num_bathrooms: 1,
  is_pet_friendly: false,
  amenities_count: 3,
};

export default function PriceEstimatorTool() {
  const [form, setForm] = useState(initialForm);
  const [cities, setCities] = useState([]);
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    propertyApi.getCities().then(({ data }) => {
      setCities(data);
      if (data.length) setForm((f) => ({ ...f, city_id: data[0].id }));
    });
  }, []);

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const handleEstimate = async (e) => {
    e.preventDefault();
    if (!form.city_id) return toast.error("Please select a city");
    setLoading(true);
    setEstimate(null);
    try {
      const { data } = await mlApi.estimatePrice({
        city_id: parseInt(form.city_id),
        size_m2: parseFloat(form.size_m2),
        num_rooms: parseInt(form.num_rooms),
        num_bathrooms: parseInt(form.num_bathrooms),
        is_pet_friendly: form.is_pet_friendly,
        amenities_count: parseInt(form.amenities_count),
      });
      setEstimate(data);
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Could not get estimate");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input form */}
      <form onSubmit={handleEstimate} className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">AI Price Estimator</h2>
          <p className="text-sm text-gray-500">
            Powered by a GradientBoosting model trained on 10,000 rental records.
            Enter property details to get a suggested monthly rent.
          </p>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700">City</label>
          <select
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={form.city_id}
            onChange={(e) => set("city_id", e.target.value)}
          >
            {cities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Input label="Size (sq ft)" type="number" min="100" value={form.size_m2} onChange={(e) => set("size_m2", e.target.value)} />
          <Input label="Amenities count" type="number" min="0" max="15" value={form.amenities_count} onChange={(e) => set("amenities_count", e.target.value)} />
          <Input label="Rooms" type="number" min="1" value={form.num_rooms} onChange={(e) => set("num_rooms", e.target.value)} />
          <Input label="Bathrooms" type="number" min="1" value={form.num_bathrooms} onChange={(e) => set("num_bathrooms", e.target.value)} />
        </div>

        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input type="checkbox" checked={form.is_pet_friendly} onChange={(e) => set("is_pet_friendly", e.target.checked)} />
            Pet-friendly
          </label>
        </div>

        <Button type="submit" loading={loading} className="w-full">Estimate Price</Button>
      </form>

      {/* Result panel */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 flex items-center justify-center">
        {loading ? (
          <div className="flex flex-col items-center gap-3 text-gray-500">
            <Spinner size="lg" />
            <p className="text-sm">Running the model…</p>
          </div>
        ) : estimate ? (
          <div className="w-full text-center space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">AI Suggested Price</p>
            <p className="text-4xl font-bold text-brand-700">
              ${estimate.suggested_price.toLocaleString()}
              <span className="text-base font-normal text-gray-500">/mo</span>
            </p>
            <div className="rounded-lg bg-brand-50 px-4 py-3">
              <p className="text-sm text-brand-700">
                Recommended range: <span className="font-semibold">${estimate.min_price.toLocaleString()} – ${estimate.max_price.toLocaleString()}</span>
              </p>
            </div>
            <p className="text-xs text-gray-400">Model version {estimate.model_version}</p>
          </div>
        ) : (
          <p className="text-sm text-gray-400 text-center">
            Fill in the property details and click <strong>Estimate Price</strong> to see the AI's suggested rent.
          </p>
        )}
      </div>
    </div>
  );
}
