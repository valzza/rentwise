import { useState } from "react";
import { Link } from "react-router-dom";
import Badge from "./ui/Badge";
import { useAuth } from "../hooks/useAuth";
import { savedPropertiesApi } from "../api/savedPropertiesApi";
import toast from "react-hot-toast";

const statusColor = { active: "green", rented: "blue", inactive: "gray" };

export default function PropertyCard({ property, initialSaved = false, onUnsave }) {
  const { isTenant } = useAuth();
  const { id, title, price, num_rooms, size_m2, status, images, neighborhood } = property;
  const primaryImage = images?.find((img) => img.is_primary) ?? images?.[0];
  const imgSrc = primaryImage?.file_path
    ? (primaryImage.file_path.startsWith("http") ? primaryImage.file_path : `/uploads/${primaryImage.file_path}`)
    : "/placeholder-property.jpg";

  const [saved, setSaved] = useState(initialSaved);
  const [busy, setBusy] = useState(false);

  const toggleSave = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    try {
      const { data } = await savedPropertiesApi.toggle(id);
      setSaved(data.saved);
      toast.success(data.saved ? "Saved to favorites" : "Removed from favorites");
      if (!data.saved && onUnsave) onUnsave(id);
    } catch {
      toast.error("Could not update favorites");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Link to={`/properties/${id}`} className="group relative flex flex-col rounded-xl border border-gray-200 bg-white shadow-soft hover:shadow-card hover:border-brand-200 transition-all overflow-hidden">
      <div className="aspect-[4/3] overflow-hidden bg-gray-100">
        <img src={imgSrc} alt={title} className="h-full w-full object-cover transition-transform group-hover:scale-105" />
      </div>

      {isTenant && (
        <button
          onClick={toggleSave}
          aria-label={saved ? "Remove from favorites" : "Save to favorites"}
          className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-white/90 shadow-soft hover:bg-white"
        >
          <span className={saved ? "text-red-500" : "text-gray-400"}>{saved ? "♥" : "♡"}</span>
        </button>
      )}

      <div className="flex flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="line-clamp-1 text-sm font-semibold text-gray-900">{title}</h3>
          <Badge color={statusColor[status] ?? "gray"}>{status}</Badge>
        </div>
        {neighborhood && (
          <p className="flex items-center gap-1 text-xs text-gray-500">
            <span className="text-brand-500">📍</span>{neighborhood.name}
          </p>
        )}
        <p className="text-lg font-bold text-brand-600">${Number(price).toLocaleString()}<span className="text-xs font-normal text-gray-500">/mo</span></p>
        <div className="flex gap-3 text-xs text-gray-500">
          <span>{num_rooms} rooms</span>
          <span>·</span>
          <span>{size_m2} sq ft</span>
        </div>
      </div>
    </Link>
  );
}