import { useEffect, useState } from "react";
import { reviewApi } from "../api/reviewApi";
import { useAuth } from "../hooks/useAuth";
import Button from "./ui/Button";
import toast from "react-hot-toast";

function Stars({ value }) {
  return (
    <span className="text-amber-500">
      {"★".repeat(value)}<span className="text-gray-300">{"★".repeat(5 - value)}</span>
    </span>
  );
}

export default function ReviewSection({ propertyId }) {
  const { isTenant } = useAuth();
  const [reviews, setReviews] = useState([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    reviewApi.listForProperty(propertyId).then(({ data }) => setReviews(data)).catch(() => {});
  };

  useEffect(load, [propertyId]);

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await reviewApi.create({ property_id: propertyId, rating, comment });
      toast.success("Review submitted");
      setComment("");
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Could not submit review");
    } finally {
      setSubmitting(false);
    }
  };

  const avg = reviews.length
    ? (reviews.reduce((s, r) => s + r.rating, 0) / reviews.length).toFixed(1)
    : null;

  return (
    <div>
      <h3 className="mb-3 flex items-center gap-2 font-semibold text-gray-900">
        Reviews {avg && <span className="text-sm font-normal text-gray-500">({avg} avg · {reviews.length})</span>}
      </h3>

      <div className="space-y-3">
        {reviews.length === 0 && <p className="text-sm text-gray-500">No reviews yet.</p>}
        {reviews.map((r) => (
          <div key={r.id} className="rounded-lg border border-gray-200 bg-white p-3">
            <Stars value={r.rating} />
            {r.comment && <p className="mt-1 text-sm text-gray-700">{r.comment}</p>}
            <p className="mt-1 text-xs text-gray-400">{new Date(r.created_at).toLocaleDateString()}</p>
          </div>
        ))}
      </div>

      {isTenant && (
        <form onSubmit={submit} className="mt-4 space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <p className="text-sm font-medium text-gray-700">Leave a review</p>
          <select
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={rating}
            onChange={(e) => setRating(Number(e.target.value))}
          >
            {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} star{n > 1 ? "s" : ""}</option>)}
          </select>
          <textarea
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            rows={3}
            placeholder="Share your experience (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <Button type="submit" loading={submitting}>Submit review</Button>
          <p className="text-xs text-gray-400">Only tenants with a completed lease on this property can review.</p>
        </form>
      )}
    </div>
  );
}